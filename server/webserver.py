import json
import gradio as gr
import requests
from configs.config import Config
from sqlalchemy import create_engine, MetaData, Table, Column, String, Integer, select, column, insert
from typing import Optional, List, Mapping, Any
from llama_index import SQLDatabase
from llama_index import SQLStructStoreIndex
from llama_index import (
    VectorStoreIndex,
    ServiceContext,
    SimpleDirectoryReader,
)
from langchain.utilities import TextRequestsWrapper
from langchain.llms import GPT4All
from langchain.llms.base import LLM
from langchain.embeddings.base import Embeddings
from pydantic import BaseModel

prompt_template = """
Given an input question, first create a syntactically correct sqlite query to run, then look at the results of the query and return the answer. You can order the results by a relevant column to return the most interesting examples in the database.
Never query for all the columns from a specific table, only ask for a few relevant columns given the question.
Pay attention to use only the column names that you can see in the schema description. Be careful to not query for columns that do not exist. Pay attention to which column is in which table. Also, qualify column names with the table name when needed.
Use the following format:
Question: Question here
SQLQuery: SQL Query to run
SQLResult: Result of the SQLQuery
Answer: Final answer here
Only use the tables listed below.
Schema of tables:
%s

Question: %s?
SQLQuery: 
"""

CFG = Config()

class CustomLLM(LLM):

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        prompt_length = len(prompt)
        input = {
            "prompt": prompt,
            "temperature": 0,
            "max_new_tokens": 2048,
            "model": "gptj-6b",
            "stop": "\nSQLResult:"
        }
        response = TextRequestsWrapper().post("http://localhost:8000/generate", input)
        return response

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        return {"name_of_model": "custom"}

    @property
    def _llm_type(self) -> str:
        return "custom"


def prepare_data(engine):
    metadata_obj = MetaData()
    table_name = "city_stats"
    city_stats_table = Table(
        table_name,
        metadata_obj,
        Column("city_name", String(16), primary_key=True),
        Column("population", Integer),
        Column("country", String(16), nullable=False),
    )
    metadata_obj.create_all(engine)
    rows = [
        {"city_name": "Toronto", "population": 2731571, "country": "Canada"},
        {"city_name": "Tokyo", "population": 13929286, "country": "Japan"},
        {"city_name": "Berlin", "population": 600000, "country": "Germany"},
    ]
    for row in rows:
        stmt = insert(city_stats_table).values(**row)
        with engine.connect() as connection:
            connection.execute(stmt)


def llama_index_text2sql(question):
    engine = create_engine("mysql+pymysql://root:aa123456@127.0.0.1:3306/%s" % CFG.LOCAL_DB_DATABASE)
    prepare_data(engine)
    table_names = CFG.local_db.get_usable_table_names()
    tables = []
    for name in table_names:
        print("table: " + name)
        tables.append(str(name))
    sql_database = SQLDatabase(engine, include_tables=tables)
    service_context = ServiceContext.from_defaults(llm=CustomLLM())
    index = SQLStructStoreIndex(
        service_context=service_context,
        sql_database=sql_database,
    )

    engine = index.as_query_engine()
    return engine.query(question)


def raw_text2sql(question):
    db_connect = CFG.local_db.get_session("test")
    schemas = CFG.local_db.table_simple_info(db_connect)
    message = ""
    for s in schemas:
        message += str(s) + ";"
    prompt = prompt_template % (message, question)
    print("prompt: " + prompt)
    input = {
        "prompt": prompt,
        "temperature": 0,
        "max_new_tokens": 2048,
        "model": "gptj-6b",
        "stop": "\nSQLResult:"
    }
    response = requests.post("%s/generate" % CFG.MODEL_SERVER, json=input).text
    return json.loads(response)["response"]

def start():
    demo = gr.Interface(fn=llama_index_text2sql, inputs="text", outputs="text")
    # demo = gr.Interface(fn=raw_text2sql, inputs="text", outputs="text")
    demo.launch()

if __name__ == "__main__":
    start()
