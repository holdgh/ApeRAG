import json
import requests
from typing import cast
from readers.local_path_embedding import LocalPathEmbedding
from vectorstore.connector import VectorStoreConnectorAdaptor
from readers.base_embedding import get_embedding_model
from qdrant_client import QdrantClient
from llama_index.indices.query import ResponseSynthesizer
from langchain.llms.base import LLM
from langchain.utilities import TextRequestsWrapper
from llama_index.prompts.default_prompts import DEFAULT_REFINE_PROMPT_TMPL, DEFAULT_TEXT_QA_PROMPT_TMPL
from langchain import PromptTemplate
from configs.config import Config


#CFG = Config()


def test_local_path_embedding():
    ctx = {"url":"http://localhost", "port":6333, "collection":"paper", "vector_size":768, "distance":"Cosine", "timeout": 1000}
    adaptor = VectorStoreConnectorAdaptor("qdrant", ctx)
    lpm = LocalPathEmbedding(adaptor, {"model_type": "huggingface"}, input_dir="/Users/slc/Desktop/paper/")
    lpm.load_data()


def test_local_path_embedding_query(query: str):
    ctx = {"url":"http://localhost", "port":6333, "collection":"paper", "vector_size":768, "distance":"Cosine", "timeout": 1000}
    adaptor = VectorStoreConnectorAdaptor("qdrant", ctx)
    embedding, vector_size = get_embedding_model({"model_type": "huggingface"})
    vector = embedding.get_query_embedding(query)
    client = cast(QdrantClient, adaptor.connector.client)
    hits = client.search(
        collection_name="test",
        query_vector=vector,
        with_vectors=True,
        limit=5,
        consistency="majority",
        search_params={"hnsw_ef":128, "exact":False},
        )

    print("hits:", hits)


def test_local_llm_qa(query: str):
    ctx = {"url":"http://localhost", "port":6333, "collection":"paper", "vector_size":768, "distance":"Cosine", "timeout": 1000}
    adaptor = VectorStoreConnectorAdaptor("qdrant", ctx)
    embedding, vector_size = get_embedding_model({"model_type": "huggingface"})
    vector = embedding.get_query_embedding(query)
    client = cast(QdrantClient, adaptor.connector.client)

    hits = client.search(
        collection_name="test",
        query_vector=vector,
        with_vectors=True,
        limit=3,
        consistency="majority",
        search_params={"hnsw_ef":128, "exact":False},
    )

    text_chunks = []
    for hit in hits:
        text_chunks.append(hit.payload.get("text"))
    answer_text = "\n\n".join(text_chunks)

    if len(answer_text) > 1600:
        answer_text = answer_text[:1900]


    context_msg = "about database and workflows, or other topics"
    prompt = PromptTemplate.from_template(DEFAULT_REFINE_PROMPT_TMPL)
    prompt_str = prompt.format(query_str=query, existing_answer=answer_text, context_msg=context_msg)

    #prompt = PromptTemplate.from_template(DEFAULT_TEXT_QA_PROMPT_TMPL)
    #prompt_str = prompt.format(query_str=query, context_str=context_msg)
    input = {
        "prompt": prompt_str,
        "temperature": 0,
        "max_new_tokens": 2048,
        "model": "gptj-6b",
        "stop": "\nSQLResult:"
    }

    print("prompt ", prompt_str)
    print(len(prompt_str))

    llm_server = "http://127.0.0.1:8000"
    response = requests.post("%s/generate" % llm_server, json=input).text
    r = json.loads(response)["response"]
    print(r)



#test_local_path_embedding()
#test_local_path_embedding_query("what is data lake")
test_local_llm_qa("what is data lake")