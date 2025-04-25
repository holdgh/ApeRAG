import os
from typing import Dict, Any

import pandas as pd
from datasets import Dataset
from langchain_openai import ChatOpenAI
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall
)

llm_for_eval = ChatOpenAI(
    base_url=os.environ["OPENAI_API_BASE"],
    api_key=os.environ["OPENAI_API_KEY"],
    model="gpt-3.5-turbo",
    temperature=0
)

# --- Step 2: Define Your RAG System Interface ---
def my_rag_system(question: str) -> Dict[str, Any]:
    """
    TODO: Dummy RAG implementation. 生产环境请替换为真实检索 + 生成逻辑
    """
    example_answer = f"This is a placeholder answer generated for the question: '{question}'."
    example_contexts = [
        f"Placeholder context relevant to '{question}'. Context 1.",
        f"Another placeholder context for '{question}'. Context 2.",
        "A generic piece of context that might or might not be relevant.",
    ]
    return {"answer": example_answer, "contexts": example_contexts}


# --- Step 3: Create a Simple Test Dataset ---
def create_tiny_testset() -> Dataset:
    print("Creating test dataset...")
    df = pd.read_csv("./datasets/qa-1300.csv")
    df = df.head(30)
    print(f"Load dataset: len={len(df)}")
    return Dataset.from_pandas(df)


# --- Step 4: Prepare Data for Ragas Evaluation ---
def prepare_evaluation_data(ds: Dataset) -> Dataset:
    print("Preparing data for Ragas evaluation...\n")

    question_list = []
    answer_list = []
    contexts_list = []
    ground_truth_list = []

    for test_case in ds:
        question = test_case["question"]
        ground_truth = test_case["answer"]

        rag_output = my_rag_system(question)

        question_list.append(question)
        answer_list.append(rag_output["answer"])
        contexts_list.append(rag_output["contexts"])
        ground_truth_list.append(ground_truth)

    return Dataset.from_dict({
        "question": question_list,
        "answer": answer_list,
        "contexts": contexts_list,
        "ground_truth": ground_truth_list,
    })


import csv
import json
import os
from datetime import datetime
from datasets import Dataset


def print_evaluation_metrics(ds: Dataset, output_dir: str = "."):
    def preprocess_row(row):
        # 处理 contexts 列表，转换为 JSON 字符串格式
        if 'contexts' in row and isinstance(row['contexts'], list):
            row['contexts'] = json.dumps(row['contexts'], ensure_ascii=False)
        # 处理其他字段中的换行符
        for k, v in row.items():
            if isinstance(v, str):
                row[k] = v.replace('\n', '\\n')
        return row

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 生成带时间戳的文件名
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M")
    filename = f"eval-output-{timestamp}.csv"
    output_path = os.path.join(output_dir, filename)

    # 预处理数据集
    processed_ds = ds.map(preprocess_row)

    # 导出CSV
    processed_ds.to_csv(
        output_path,
        index=False,
        quoting=csv.QUOTE_ALL,
        escapechar='\\',
        doublequote=True,
        encoding='utf-8'
    )

    print(f"评估结果已导出到: {output_path}")


# --- Step 5: Run Ragas Evaluation ---
def evaluate_rag_with_ragas(dataset: Dataset):
    metrics = [faithfulness, answer_relevancy, context_precision, context_recall]
    results = evaluate(
        dataset=dataset,
        metrics=metrics,
        llm=llm_for_eval,
        raise_exceptions=False
    )
    return results


# --- Main Execution Block ---
def display_results(evaluation_results: Dataset):
    if not evaluation_results:
        print("[Error] Ragas evaluation failed.")
        return

    print("\n--- RAGAS 评分汇总 ---")
    metrics = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]
    avg = {m: round(sum(evaluation_results[m]) / len(evaluation_results[m]), 4) for m in metrics}
    for k, v in avg.items():
        print(f"{k:<18}: {v}")

    pd.set_option("display.max_colwidth", 200)
    pd.set_option("display.width", 120)
    print(evaluation_results.to_pandas())


if __name__ == "__main__":
    print("--- RAG System Evaluation Script ---")
    ds = create_tiny_testset()
    eval_dataset = prepare_evaluation_data(ds)
    print_evaluation_metrics(eval_dataset)
    print("[Info] Evaluation input written to ragas_input.csv")

    eval_results = evaluate_rag_with_ragas(eval_dataset)
    display_results(eval_results)

    print("\n--- Script execution finished ---")