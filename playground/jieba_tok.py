import os

import jieba
import jieba.analyse
import jieba.posseg as pseg


def prepare_queries(test_cases_path):
    files = []
    # r=root, d=directories, f = files
    for r, d, f in os.walk(test_cases_path):
        for file in f:
            files.append(file)
    return files


path = "/Users/ziang/git/KubeChat/resources/datasets/tos"

print("分词")
for q in prepare_queries(path):
    words = pseg.cut(q)
    tokens = []
    for word, flag in words:
        if flag not in ["v", "n", "eng"]:
            continue
        tokens.append(f"{word}")
    result = " ".join(tokens)
    print(f"[{q}]: {result}")


print("分词 - 搜索引擎模式")
for q in prepare_queries(path):
    tokens = []
    seg_list = jieba.cut_for_search(q)
    result = " ".join(seg_list)
    print(f"[{q}]: {result}")


print("提取关键词")
for q in prepare_queries(path):
    tokens = []
    for x, w in jieba.analyse.extract_tags(q, withWeight=True):
        tokens.append(x)
    result = " ".join(tokens)
    print(f"[{q}]: {result}")

