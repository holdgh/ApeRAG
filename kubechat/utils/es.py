import os

from elasticsearch import Elasticsearch

from kubechat.utils.full_text import insert_document, search_document, get_index_name

es = Elasticsearch(hosts="http://127.0.0.1:9200")

col_id = "3"


def prepare_datasets(test_cases_path):
    test_cases = []
    files = []
    # r=root, d=directories, f = files
    for r, d, f in os.walk(test_cases_path):
        for file in f:
            files.append(os.path.join(r, file))
    for idx, file in enumerate(files):
        name = os.path.basename(file)
        with open(file) as f:
            data = f.read()
        insert_document(col_id, idx, name, data)
    return test_cases


# prepare_datasets("/Users/ziang/git/KubeChat/resources/documents/tos-feishu-parser-markdown")


# insert_document(col_id, "1", "Release v1.0.2发布文档", content)
# search_document(["v1.0.2"])
# search_document(["功能", "修复"])
# search_document(["功能", "修复", "阻", "试"])
# print(search_document(col_id, ["TOS", "延迟", "启动"]))
# print(search_document(col_id, ["延迟", "启动"]))
# print(search_document(col_id, ["延迟", "启"]))
# print(search_document(col_id, ["延迟启动"]))
# print(search_document(col_id, ["介绍", "延迟启动"]))
print(search_document(col_id, []))
# tokens = es.indices.analyze(index="collection-2", body={"text": content}, analyzer="ik_max_word")
tokens = es.indices.analyze(index=get_index_name(col_id), body={"text": "介绍一下TOS的延迟启动"},
                            analyzer="ik_max_word")
print(tokens)
