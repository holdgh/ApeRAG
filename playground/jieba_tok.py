import os

import jieba.posseg as pseg


def prepare_queries(test_cases_path):
    files = []
    # r=root, d=directories, f = files
    for r, d, f in os.walk(test_cases_path):
        for file in f:
            files.append(file)
    return files


path = "/Users/ziang/git/KubeChat/resources/datasets/tos"
for q in prepare_queries(path):
    words = pseg.cut(q)
    tokens = []
    for word, flag in words:
        if flag not in ["v", "n", "eng"]:
            continue
        tokens.append(f"{word}")
    result = " ".join(tokens)
    print(f"[{q}]: {result}")
