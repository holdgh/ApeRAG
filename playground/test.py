import json

import requests
from langchain import PromptTemplate

query_str = "如何在windows中安装kbcli?"
'''
you can custom your own prompt
'''
prompt_template = """
上下文信息如下:
----------------
{context}
--------------

根据提供的上下文信息,然后回答问题：{query}。

请确保回答准确和详细。
"""
prompt = PromptTemplate.from_template(prompt_template)
prompt_str = prompt.format(query=query_str, context="none")

LLM_API = "http://a780a53170a7140f58efd575b03d60b5-667ac4219aac185d.elb.ap-northeast-1.amazonaws.com:8000/generate_stream"
data = {
    "prompt": prompt_str,
}
response = requests.post(LLM_API, json=data,stream=True)
for chunk in response.iter_lines(chunk_size=2048, decode_unicode=False, delimiter=b"\0"):
    if chunk:
        data = json.loads(chunk.decode("utf-8"))
        print(data)

