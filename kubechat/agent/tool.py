from langchain.tools import BaseTool
import json
import requests
import os
import re
from langchain_community.vectorstores import FAISS
os.environ['BEARER_TOKEN'] = ""
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document
# class CountTool(BaseTool):
#     def _run(self, data = None):
#         try:
#             json_data = json.loads(data)
#         except:
#             return "输入格式有误，必须是json格式的数据，不包括其他信息"
        

class APIDefinition(BaseTool):
    url: str
    method: str
    return_direct = False
    before_need_tool: list = []
    before_prompt: str = "输入有误，请先调用工具：{before_need_tool}"
    bearer_token = os.getenv('BEARER_TOKEN')
    tool_index : list = []
    
    def get_tool_index(self):
        return self.tool_index
    
    def _run(self, data = None):
        
        arg_match = re.findall(r'\{([^}]+)\}', self.url)
            
        data = data.replace("\\","").replace("\"","").replace("，",",").replace("\'","").replace(' ','')
        start = data.find('[')
        end = data.rfind(']') if data.rfind(']') != -1 else len(data)
        input_datas = data[start+1:end].split(',')
        if input_datas == ['']:
            input_datas = []
        
        before = "输入参数为list格式，需要以逗号分隔，分别代表：{arg_match}，不包括其他无关表达。".format(arg_match = str(arg_match))
        after = self.before_prompt.format(before_need_tool = str(self.before_need_tool))
        headers = {'Authorization': f'Bearer {self.bearer_token}'}
        if arg_match == ['orgName']:    
            response = requests.get("https://api-dev.apecloud.cn/api/v1/organizations", headers=headers)
            input_datas = [json.loads(response.text)["items"][0]["name"]]

        try:
            kwargs = {arg:input_data for arg, input_data in zip(arg_match, input_datas)}
            url = self.url.format(**kwargs)
        except:
            return  before + after   
                
        if self.method == "get":
            response = requests.get(url, headers=headers)
        else:
            raise ValueError("Unsupported HTTP method")
        try:
            answer = json.loads(response.text)
            if answer.get("error",None) != None:
                return before+after
            else:
                return response.text
        except:
            if response.text == "":
                return before+after
            else:
                return response.text

class SeleceTools():
    def __init__(self, url, file) -> None:
        self.url = url
        self.file = file
        self.tools = []
        self.create_tools()
    
    def before_need_tool(self,url):
        arg_match = re.findall(r'\{([^}]+)\}', url)
        url_match = re.finditer(r'([^{}]+)(?:\{[^{}]+\})?', url)
        results = [match.group(1)[:-1] for match in url_match]
        tool_name = []
        tool_index = []
        index = -1
        for result in results:
            for path, data in self.api_table["paths"].items():
                for way, info in data.items():
                    if way !='get' or info.get("operationId",None) == None or info.get("description",None) == None:
                    # if way !='get' or info.get("operationId",None) == None:
                        continue
                    index += 1
                    if path != result:
                        continue
                    tool_name.append(info["operationId"])
                    tool_index.append(index)
        return tool_name, arg_match, tool_index
    
    def make_description(self,description, arg_match):
        after_description = ": 输入参数为list格式，需要以逗号分隔，分别代表：{arg_match}，不包括其他无关表达，如果没有输入参数，请输入[]".format(arg_match = str(arg_match))
        if arg_match == []:
            return description
        else:
            return description+after_description
        
    def create_tools(self):
        with open(self.file, 'r', encoding='utf-8') as file:
            self.api_table = json.load(file)

        # 根据 API 表格数据创建基类
        for path, data in self.api_table["paths"].items():
            for way, info in data.items():
                if way !='get' or info.get("operationId",None) == None or info.get("description",None) == None:
                # if way !='get' or info.get("operationId",None) == None:
                    continue
                before_need_tool, arg_match, tool_index = self.before_need_tool(path)
                description = self.make_description(info.get("description",""), arg_match)
                tool_class = APIDefinition(name = info["operationId"], 
                                            description = description,
                                            method = way,
                                            url = self.url + path,
                                            before_need_tool=before_need_tool,
                                            tool_index = tool_index)
                self.tools.append(tool_class)
        
        docs = [Document(page_content=t.description, metadata={"index": i, "tool_index":t.get_tool_index()}) for i, t in enumerate(self.tools)]
        self.vector_store = FAISS.from_documents(docs, OpenAIEmbeddings())
        self.retriever = self.vector_store.as_retriever()
    
    def select(self, input):
        docs = self.retriever.get_relevant_documents(input)
        select_tool_index = set()
        for d in docs:
            select_tool_index.add(d.metadata["index"])
            select_tool_index.update(d.metadata["tool_index"])
        return [self.tools[i] for i in select_tool_index]

    def get_tools(self):
        return self.tools
    
    def make_run(self, operate, context):
        for tool in self.tools:
            if tool.name == operate:
                return tool._run(context)
    
    