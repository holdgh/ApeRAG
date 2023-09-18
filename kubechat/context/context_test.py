import os
import sys

from tabulate import tabulate
from datetime import datetime

from kubechat.context.context import ContextManager
from kubechat.llm.predict import CustomLLMPredictor
from readers.base_embedding import get_embedding_model
from readers.local_path_embedding import LocalPathEmbedding
from vectorstore.connector import VectorStoreConnectorAdaptor

VECTOR_DB_TYPE = "qdrant"
VECTOR_DB_CONTEXT = {"url": "http://127.0.0.1", "port": 6333, "distance": "Cosine", "timeout": 1000}


table_format = """
<html>
<head>
<style> 
  table {{ table-layout: fixed; border: 1px solid black; border-collapse: collapse; }}
  th {{ border: 1px solid black; border-collapse: collapse; white-space:break-spaces; overflow:hidden; position:sticky; top: 0; padding: 5px;}}
  td {{ border: 1px solid black; border-collapse: collapse; white-space:break-spaces; overflow:hidden; padding: 5px; word-wrap: break-all}}
</style>
</head>
{table}
</body></html>
"""


class TestCase:
    def __init__(self, query, expect):
        self.query = query
        self.expect = expect


class EmbeddingCtx:
    def __init__(self, collection_name, model_name):
        self.model_name = model_name
        self.model, self.vector_size = get_embedding_model(model_name)
        self.collection_name = f"{collection_name}_{model_name}_{self.vector_size}"
        ctx = VECTOR_DB_CONTEXT.copy()
        ctx["collection"] = self.collection_name
        self.ctx_manager = ContextManager(self.collection_name, self.model, VECTOR_DB_TYPE, ctx)
        self.vector_db_conn = VectorStoreConnectorAdaptor(VECTOR_DB_TYPE, ctx=ctx)

        self.qa_collection_name = f"{self.collection_name}-qa"
        qa_ctx = VECTOR_DB_CONTEXT.copy()
        qa_ctx["collection"] = self.qa_collection_name
        self.qa_ctx_manager = ContextManager(self.qa_collection_name, self.model, VECTOR_DB_TYPE, qa_ctx)
        self.qa_vector_db_conn = VectorStoreConnectorAdaptor(VECTOR_DB_TYPE, ctx=qa_ctx)

    def load_file(self, file_path):
        loader = LocalPathEmbedding(input_files=[file_path], embedding_model=self.model,
                                    vector_store_adaptor=self.vector_db_conn)
        loader.load_data()

        predictor = CustomLLMPredictor(model="baichuan-13b", endpoint="http://localhost:18000")
        # qa_loader = LocalPathQAEmbedding(predictor=predictor, input_files=[file_path], embedding_model=self.model,
        #                                  vector_store_adaptor=self.qa_vector_db_conn)
        # qa_loader.load_data()

    def load_dir(self, path):
        self.vector_db_conn.connector.create_collection(vector_size=self.vector_size)
        self.qa_vector_db_conn.connector.create_collection(vector_size=self.vector_size)
        files = []
        # r=root, d=directories, f = files
        for r, d, f in os.walk(path):
            for file in f:
                files.append(os.path.join(r, file))

        for file in files:
            self.load_file(file)

    def query(self, query, **kwargs):
        # results = self.qa_ctx_manager.query(query, score_threshold=0.8, topk=3, recall_factor=1)
        # if len(results) > 0:
        #     return results
        return self.ctx_manager.query(query, **kwargs)


def prepare_datasets(test_cases_path):
    test_cases = []
    files = []
    # r=root, d=directories, f = files
    for r, d, f in os.walk(test_cases_path):
        for file in f:
            files.append(os.path.join(r, file))
    for file in files:
        query = os.path.basename(file)
        with open(file) as f:
            references = f.read()
        test_cases.append(TestCase(query, references))
    return test_cases


def prepare_documents(dataset_dir, models, reload=False):
    ctx_list = []
    for model in models:
        ctx = EmbeddingCtx(os.path.basename(dataset_dir), model)
        ctx_list.append(ctx)
        if reload:
            ctx.load_dir(dataset_dir)
    return ctx_list


def compare_models(test_cases, embedding_ctxs, **kwargs):
    table = []
    for i, item in enumerate(test_cases):
        row = [item.query, item.expect]
        for ctx in embedding_ctxs:
            results = ctx.query(item.query, **kwargs)
            candidates = []
            for result in results:
                candidates.append(f"{result.score}: {result.text}")
            row.append("\n\n".join(candidates))
        table.append(row)
    return table


"""
class Logger:
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log = open(filename, "w")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        self.terminal.flush()
        self.log.flush()

    def isatty(self):
        return False


sys.stdout = Logger("output.log")


def test(x):
    print("This is a test")
    print(f"Your function is running with input {x}...")
    return x


def read_logs():
    sys.stdout.flush()
    with open("output.log", "r") as f:
        return f.read()


import gradio as gr

def tax_calculator(income, marital_status, assets):
    tax_brackets = [(10, 0), (25, 8), (60, 12), (120, 20), (250, 30)]
    total_deductible = sum(assets["Cost"])
    taxable_income = income - total_deductible

    total_tax = 0
    for bracket, rate in tax_brackets:
        if taxable_income > bracket:
            total_tax += (taxable_income - bracket) * rate / 100

    if marital_status == "Married":
        total_tax *= 0.75
    elif marital_status == "Divorced":
        total_tax *= 0.8

    return round(total_tax)

demo = gr.Interface(
    tax_calculator,
    [
        "number",
        gr.Radio(["Single", "Married", "Divorced"]),
        gr.Dataframe(
            headers=["Item", "Cost"],
            datatype=["str", "number"],
            label="Assets Purchased this Year",
        ),
    ],
    "number",
    examples=[
        [10000, "Married", [["Suit", 5000], ["Laptop", 800], ["Car", 1800]]],
        [80000, "Single", [["Suit", 800], ["Watch", 1800], ["Car", 800]]],
    ],
)

demo.launch()



def build_web_demo():

    with gr.Blocks(
        title="Embedding Comparison",
        theme=gr.themes.Base(),
    ) as demo:
        score_threshold = gr.Slider(0, 1, value=0.5, label="ScoreThreshold", info="Only show results with score higher than this threshold")
        topk = gr.Slider(1, 100, value=3, label="TopK", info="Only show top K results")
        documents = gr.Dropdown(
            [
                "/Users/ziang/git/kubechat/resources/documents/tos-feishu-export-pdf",
                "/Users/ziang/git/kubechat/resources/documents/tos-feishu-parser-plain",
                "/Users/ziang/git/kubechat/resources/documents/tos-feishu-plain-api",
                "/Users/ziang/git/kubechat/resources/documents/plain",
                "/Users/ziang/git/kubechat/resources/documents/test",
            ],
            label="Documents"
        )
        datasets = gr.Dropdown(
            [
                "/Users/ziang/git/KubeChat/resources/datasets/test",
                "/Users/ziang/git/KubeChat/resources/datasets/tos",
            ],
            label="Datasets"
        )
        models = gr.CheckboxGroup(["text2vec", "bge", "openai"], label="Embedding Models")
        btn = gr.Button("Run")
        txt_3 = gr.Textbox(value="", label="Output")
        btn.click(main, inputs=[datasets, documents, models, score_threshold, topk], outputs=[txt_3])
        logs = gr.Textbox()
        demo.load(read_logs, None, logs, every=1)
    return demo
"""


def main(datasets, documents, models, reload, **kwargs):
    datasets = prepare_datasets(datasets)
    ctx_list = prepare_documents(documents, models, reload)
    table = compare_models(datasets, ctx_list, **kwargs)
    headers = ["query", "references"]
    for i, ctx in enumerate(ctx_list):
        headers.append(ctx.model_name)
    return headers, table


os.environ["ENABLE_QA_GENERATOR"] = "True"


if __name__ == "__main__":
    # datasets = "/Users/ziang/git/KubeChat/resources/datasets/tos"
    # datasets = "/Users/ziang/git/KubeChat/resources/datasets/releases"
    datasets = "/Users/ziang/git/KubeChat/resources/datasets/test1"
    # documents = "/Users/ziang/git/kubechat/resources/documents/test"
    # documents = "/Users/ziang/git/KubeChat/resources/documents/tos-feishu-bad-cases-plain"
    # documents = "/Users/ziang/git/KubeChat/resources/documents/tos-feishu-bad-cases-markdown"
    documents = "/Users/ziang/git/KubeChat/resources/documents/tos-feishu-parser-markdown"
    # documents = "/Users/ziang/git/KubeChat/resources/documents/releases"
    # documents = "/Users/ziang/git/KubeChat/resources/documents/tos-feishu-parser-markdown-2"
    # documents = "/Users/ziang/git/KubeChat/resources/documents/tos-short"
    # documents = "/Users/ziang/git/kubechat/resources/documents/tos-feishu-parser-plain"
    # documents = "/Users/ziang/git/kubechat/resources/documents/tos-feishu-parser-plain-without-category"
    # documents = "/Users/ziang/git/kubechat/resources/documents/tos-pdf"
    # models = ["multilingual"]
    # models = ["text2vec"]
    models = ["bge"]
    # models = ["mt5"]
    # models = ["openai"]
    # models = ["text2vec", "bge"]
    # models = ["text2vec", "bge", "multilingual", "openai"]
    # models = ["text2vec", "bge", "piccolo"]
    # models = ["piccolo"]
    score_threshold = 0.5
    topk = 3
    recall_factor = 10
    reload = True
    headers, table = main(datasets, documents, models, reload,
                          score_threshold=score_threshold,
                          topk=topk,
                          recall_factor=recall_factor)
    result = table_format.format(table=tabulate(table, headers, tablefmt="html")).encode("utf-8")
    result_path = f'/tmp/{os.path.basename(documents)}-{datetime.utcnow().timestamp()}.html'
    with open(result_path, "wb+") as fd:
        fd.write(result)
    print(f"write output to file: {result_path}")

    # build_web_demo().queue().launch()
