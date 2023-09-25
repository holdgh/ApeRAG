import os

from huggingface_hub import hf_hub_download, snapshot_download
from langchain.embeddings import HuggingFaceBgeEmbeddings
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM


if __name__ == "__main__":
    repo_is = [
        "BAAI/bge-large-zh",
    ]
    os.environ['CURL_CA_BUNDLE'] = ''
    os.environ.setdefault("https_proxy", "socks5://127.0.0.1:34001")

    embedding_model = HuggingFaceBgeEmbeddings(
        model_name="BAAI/bge-large-zh-v1.5",
    )

    # from text2vec import SentenceModel
    # model_name = "GanymedeNil/text2vec-large-chinese"
    # model = SentenceModel(model_name)
    # tokenizer = AutoTokenizer.from_pretrained(model_name)
    # model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

    # for repo_id in repo_is:
    #     print("repo:", repo_id)
    #     snapshot_download(repo_id=repo_id)
