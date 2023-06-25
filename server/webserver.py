import gradio as gr
import requests
from configs.config import Config

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
Schema of all tables:
%s

Question: %s?
SQLQuery: 
"""

CFG = Config()

def greet(question):
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
    return requests.post("http://localhost:8000/generate", json=input).text

def start():
    demo = gr.Interface(fn=greet, inputs="text", outputs="text")
    demo.launch()   

if __name__ == "__main__":
    start()
