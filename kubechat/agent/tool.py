import ast
import json
import os
import re
import logging
logger = logging.getLogger(__name__)

import requests
from langchain.tools import BaseTool
from langchain_community.vectorstores import FAISS

from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings


class APIDefinition(BaseTool):
    url: str
    method: str
    return_direct = False
    before_need_tool: list = []
    before_prompt: str = "输入有误，请先调用工具：{before_need_tool}"
    bearer_token : str
    tool_index: list = []
    payload: list = []
    
    def get_tool_index(self):
        return self.tool_index
    
    def make_data(self, data, arg_match):
        try:
            input_datas = ast.literal_eval(data)
        except:
            data = data.replace("\\", "").replace("\"", "").replace("，", ",").replace("\'", "").replace(' ', '')
            start = data.find('[')
            end = data.rfind(']') if data.rfind(']') != -1 else len(data)
            input_datas = data[start + 1:end].split(',')
        if input_datas == ['']:
            input_datas = []
        
        if 'orgName' in arg_match:
            try:
                headers = {'Authorization': f'Bearer {self.bearer_token}'}
                response = requests.get("https://api-dev.apecloud.cn/api/v1/organizations", headers=headers)
                orgName = json.loads(response.text)["items"][0]["name"]
                if input_datas == []:
                    input_datas = [orgName]
                else:
                    input_datas[0] = orgName
            except:
                logger.error("Failed to get organization name")            
        return input_datas
    
    def make_url(self, data, arg_match):
        try:
            kwargs = {arg: input_data for arg, input_data in zip(arg_match, data[:len(arg_match)])}
            url = self.url.format(**kwargs)
            json_payload = {arg: input_data for arg, input_data in zip(self.payload, data[len(arg_match):])}
            return url, json_payload
        except:
            return "", ""
        
    def make_answer(self, response, bad_answer):
        # if self.method == "post" and response.status_code == 202:
        #     return "该操作已完成。"
        try:
            answer = json.loads(response.text)
        except:
            return bad_answer
        if answer.get("error", None) == None and response.text != "":
            return '操作已完成，响应是：' + response.text
        else:
            return bad_answer
        
    def _run(self, data=None):
        arg_match = re.findall(r'\{([^}]+)\}', self.url)
        input_datas = self.make_data(data, arg_match)
        url, json_payload = self.make_url(input_datas, arg_match)
        
        arg_match.extend(self.payload)
        # bad_answer = "输入参数为list格式，需要以逗号分隔，分别代表：{arg_match}，不包括其他无关表达。".format(arg_match = str(arg_match)) + self.before_prompt.format(before_need_tool = str(self.before_need_tool))
        bad_answer = self.description + self.before_prompt.format(before_need_tool=str(self.before_need_tool))
        if url == "":
            return bad_answer
        
        headers = {'Authorization': f'Bearer {self.bearer_token}'}         
        if self.method == "get":
            response = requests.get(url, headers=headers)
        elif self.method == "post":
            response = requests.post(url, headers=headers, json=json_payload)
        else:
            raise ValueError("Unsupported HTTP method")
        
        answer = self.make_answer(response, bad_answer)
        return answer

class SeleceTools():
    def __init__(self, url, file, bearer_token) -> None:
        self.url = url
        self.file = file
        self.tools = []
        self.bearer_token = bearer_token
        self.create_tools()
        
    def check(self, way, info):
        if (way != 'get' and way != 'post') or info.get("operationId", None) == None or info.get("description", None) == None:
            return False
        if way == 'post' and info.get("payload", None) == None:
            return False
        return True
        
    def before_need_tool(self, url):
        arg_match = re.findall(r'\{([^}]+)\}', url)
        url_match = re.finditer(r'([^{}]+)(?:\{[^{}]+\})?', url)
        results = [match.group(1)[:-1] for match in url_match]
        tool_name = []
        tool_index = []
        index = -1
        for result in results:
            for path, data in self.api_table["paths"].items():
                for way, info in data.items():
                    if not self.check(way, info):
                        continue
                    index += 1
                    if path != result:
                        continue
                    tool_name.append(info["operationId"])
                    tool_index.append(index)
        return tool_name, arg_match, tool_index
    
    def make_description(self, description, arg_match):
        # after_description = ": 输入参数为list格式，需要以逗号分隔，分别代表：{arg_match}，不包括其他无关表达，如果没有输入参数，请输入[]".format(arg_match = str(arg_match))
        after_description = ""
        if arg_match == []:
            return description
        else:
            return description + after_description
        
    def create_tools(self):
        with open(self.file, 'r', encoding='utf-8') as file:
            self.api_table = json.load(file)

        # 根据 API 表格数据创建基类
        for path, data in self.api_table["paths"].items():
            for way, info in data.items():
                if not self.check(way, info):
                    continue
                    
                before_need_tool, arg_match, tool_index = self.before_need_tool(path)
                payload = info.get("payload", [])
                arg_match.extend(payload)
                
                description = self.make_description(info.get("description", ""), arg_match)
                tool_class = APIDefinition(name=info["operationId"], 
                                            description=description,
                                            method=way,
                                            url=self.url + path,
                                            bearer_token = self.bearer_token,
                                            before_need_tool=before_need_tool,
                                            tool_index=tool_index,
                                            payload=payload
                                            )
                self.tools.append(tool_class)
        
        docs = [Document(page_content=t.description, metadata={"index": i, "tool_index": t.get_tool_index()}) for i, t in enumerate(self.tools)]
        self.vector_store = FAISS.from_documents(docs, OpenAIEmbeddings())
        self.retriever = self.vector_store.as_retriever()
    
    def select(self, input):
        docs = self.retriever.get_relevant_documents(input)
        select_tool_index = set()
        for d in docs:
            select_tool_index.add(d.metadata["index"])
            select_tool_index.update(d.metadata["tool_index"])
        select_tools = [self.tools[i] for i in select_tool_index]
        tool_names = ", ".join([tool.name for tool in select_tools])
        tool_strings = "\n".join([f"> {tool.name}: {tool.description}" for tool in select_tools])
        return tool_names, tool_strings

    def get_tools(self):
        return self.tools
    
    def make_run(self, operate, context):
        for tool in self.tools:
            if tool.name == operate:
                return tool._run(context)
    
    