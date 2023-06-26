import logging
import sys
from langchain.llms import GPT4All
from sqlalchemy import create_engine, MetaData, Table, Column, String, Integer
from llama_index import SQLStructStoreIndex, SQLDatabase, ServiceContext
from llama_index import LLMPredictor
from sqlalchemy import insert

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))

local_llm_path = '/Users/alal/KubeChat/ggml-gpt4all-j-v1.3-groovy.bin'
llm = GPT4All(model=local_llm_path, n_ctx=512)
llm_predictor = LLMPredictor(llm=llm)

engine = create_engine("sqlite:///:memory:")
metadata_obj = MetaData()

user_table = Table(
    "user",
    metadata_obj,
    Column("user_name", String(16), primary_key=True),
    Column("age", Integer),
)

user_table = Table(
    "good",
    metadata_obj,
    Column("good name", String(16), primary_key=True),
    Column("price", Integer),
)

metadata_obj.create_all(engine)

sql_database = SQLDatabase(engine, include_tables=["user", "good"])
# print(sql_database.table_info)
sc = ServiceContext.from_defaults(llm=llm)
index = SQLStructStoreIndex(
    service_context=sc,
    sql_database=sql_database,
)
server_context = ServiceContext.from_defaults(llm_predictor=llm_predictor)
query_engine = index.as_query_engine()
response = query_engine.query("Who have the largest age in the user table")
print(response)


# def process_database_question(database_name, llm):
#     embeddings = OpenAIEmbeddings() if openai_use else HuggingFaceEmbeddings(model_name=ingest_embeddings_model)
#     persist_dir = f"./db/{database_name}"
#     db = Chroma(persist_directory=persist_dir, embedding_function=embeddings, client_settings=Settings(
#         chroma_db_impl='duckdb+parquet',
#         persist_directory=persist_dir,
#         anonymized_telemetry=False
#     ))
#
#     retriever = db.as_retriever(search_kwargs={
#         "k": ingest_target_source_chunks if ingest_target_source_chunks else args.ingest_target_source_chunks})
#
#     template = """You are a an AI assistant providing helpful advice. You are given the following extracted parts of a long document and a question.
#     Provide a conversational answer based on the context provided. If you can't find the answer in the context below, just say
#     "Hmm, I'm not sure." Don't try to make up an answer. If the question is not related to the context, politely respond
#     that you are tuned to only answer questions that are related to the context.
#
#     Question: {question}
#     =========
#     {context}
#     =========
#     Answer:"""
#     question_prompt = PromptTemplate(template=template, input_variables=["question", "context"])
#
#     qa = ConversationalRetrievalChain.from_llm(llm=llm, condense_question_prompt=question_prompt, retriever=retriever,
#                                                chain_type="stuff", return_source_documents=not args.hide_source)
#     return qa