from typing import List
from elasticsearch import Elasticsearch

from config import settings

es = Elasticsearch(settings.ES_HOST)


# import redis
from redisearch.client import Client, Query, IndexDefinition
from redisearch import TextField
# from redis.commands.search.query import Query
# from redis.commands.json.path import Path
# from redis.commands.search.field import TextField
# from redis.commands.search.indexDefinition import IndexDefinition, IndexType

from config.settings import REDIS_HOST, REDIS_PORT, REDIS_USERNAME, REDIS_PASSWORD


# def get_redis_client() -> redis.Redis:
#     return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, username=REDIS_USERNAME, password=REDIS_PASSWORD, decode_responses=True)
#

# def insert_document(collection_id, doc_id, doc_name, contentgg):
#     r = get_redis_client()
#     rs = r.ft(f"collection:fulltext:{collection_id}")
#     try:
#         schema = (
#             TextField("$.name", as_name="name"),
#             TextField("$.content", as_name="content"),
#         )
#         rs.create_index(schema, definition=IndexDefinition(prefix=["document:"], index_type=IndexType.JSON))
#     except redis.ResponseError as e:
#         if "Index already exists" not in str(e):
#             raise e
#     doc = {
#         "name": doc_name,
#         "content": content,
#     }
#     r.json().set(f"document:{doc_id}", Path.root_path(), doc)

# def search_document(collection_id: str, keywords: List[str]):
#     r = get_redis_client()
#     rs = r.ft(f"collection:fulltext:{collection_id}")
#     query = Query(" ".join(keywords)).language("chinese")
#     docs = rs.search(query).docs
#     return docs

# def search_document(collection_id: str, keywords: List[str]):
#     client = Client(f"collection:fulltext:{collection_id}")
#     docs = client.search(Query(' '.join(keywords))).docs
#     return docs
#
#
# def insert_document(collection_id, doc_id, doc_name, content):
#     client = Client(f"collection:fulltext:{collection_id}")
#     try:
#         definition = IndexDefinition(prefix=[f"collection:{collection_id}:document:"])
#         client.create_index([TextField('name'), TextField('content')],
#                             definition=definition, stopwords=",<>{}[]\"':;!@#$%^&*()-+=~")
#     except redis.ResponseError as e:
#         if "Index already exists" not in str(e):
#             raise e
#
#     client.add_document(f"collection:{collection_id}:document:{doc_id}", language="chinese", name=doc_name, content=content)
#


def get_index_name(collection_id):
    return f"collection-{collection_id}"


# insert document into elasticsearch
def insert_document(collection_id, doc_id, doc_name, content):
    doc = {
        'name': doc_name,
        'content': content,
    }
    index = get_index_name(collection_id)
    if not es.indices.exists(index=index).body:
        es.indices.create(index=index)
        es.indices.put_mapping(index=index, properties={
            "content": {
                "type": "text",
                "analyzer": "ik_max_word",
                "search_analyzer": "ik_smart"
            }
        })
    es.index(index=index, id=f"{doc_id}", document=doc)


def remove_document(collection_id, doc_id):
    index = get_index_name(collection_id)
    es.delete(index=index, id=f"{doc_id}")


def search_document(collection_id: str, keywords: List[str], topk=3):
    index = get_index_name(collection_id)
    query = {
        "bool": {
            "should": [
                {"match": {"content": keyword}} for keyword in keywords
            ],
            "minimum_should_match": "80%",
            # "minimum_should_match": "-1",
        },
    }
    sort = [
        {
            "_score": {
                "order": "desc"
            }
        }
    ]
    resp = es.search(index=index, query=query, sort=sort, size=topk)
    hits = resp.body["hits"]
    result = []
    for hit in hits["hits"]:
        result.append(hit["_source"])
    return result

