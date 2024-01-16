from langchain.tools import BaseTool
import json
import requests
import os
import re
from langchain_community.vectorstores import FAISS
os.environ['BEARER_TOKEN'] = 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6InlBa0ZPbkF3MTVfdzRTeW5wM1FNVEMzN2hpdHJLVWIxQms1dVdFMWtlNlUifQ.eyJ1cGRhdGVkX2F0IjoiMjAyNC0wMS0wOFQxMzowNjo0NS40MDVaIiwiYWRkcmVzcyI6eyJjb3VudHJ5IjpudWxsLCJwb3N0YWxfY29kZSI6bnVsbCwicmVnaW9uIjpudWxsLCJmb3JtYXR0ZWQiOm51bGx9LCJwaG9uZV9udW1iZXJfdmVyaWZpZWQiOmZhbHNlLCJwaG9uZV9udW1iZXIiOm51bGwsImxvY2FsZSI6bnVsbCwiem9uZWluZm8iOm51bGwsImJpcnRoZGF0ZSI6bnVsbCwiZ2VuZGVyIjoiVSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJlbWFpbCI6Imdhb21qQGJ1cHQuZWR1LmNuIiwid2Vic2l0ZSI6bnVsbCwicGljdHVyZSI6Imh0dHBzOi8vZmlsZXMuYXV0aGluZy5jby9hdXRoaW5nLWNvbnNvbGUvZGVmYXVsdC11c2VyLWF2YXRhci5wbmciLCJwcm9maWxlIjpudWxsLCJwcmVmZXJyZWRfdXNlcm5hbWUiOm51bGwsIm5pY2tuYW1lIjpudWxsLCJtaWRkbGVfbmFtZSI6bnVsbCwiZmFtaWx5X25hbWUiOm51bGwsImdpdmVuX25hbWUiOm51bGwsIm5hbWUiOm51bGwsInN1YiI6IjY1OWJmMzQxMjI1NTViOGFmZDljZDI1MCIsImV4dGVybmFsX2lkIjpudWxsLCJ1bmlvbmlkIjpudWxsLCJ1c2VybmFtZSI6bnVsbCwiZGF0YSI6eyJ0eXBlIjoidXNlciIsInVzZXJQb29sSWQiOiI2NTRjY2NjODQ3MDYwNzZhMDg2ZDgyZWUiLCJhcHBJZCI6IjY1NGNjZDFmZGRiYTcwZTMzY2Q5ZTExNiIsImlkIjoiNjU5YmYzNDEyMjU1NWI4YWZkOWNkMjUwIiwidXNlcklkIjoiNjU5YmYzNDEyMjU1NWI4YWZkOWNkMjUwIiwiX2lkIjoiNjU5YmYzNDEyMjU1NWI4YWZkOWNkMjUwIiwicGhvbmUiOm51bGwsImVtYWlsIjoiZ2FvbWpAYnVwdC5lZHUuY24iLCJ1c2VybmFtZSI6bnVsbCwidW5pb25pZCI6bnVsbCwib3BlbmlkIjpudWxsLCJjbGllbnRJZCI6IjY1NGNjY2M4NDcwNjA3NmEwODZkODJlZSJ9LCJ1c2VycG9vbF9pZCI6IjY1NGNjY2M4NDcwNjA3NmEwODZkODJlZSIsImF1ZCI6IjY1NGNjZDFmZGRiYTcwZTMzY2Q5ZTExNiIsImV4cCI6MTcwNTkyODgxMCwiaWF0IjoxNzA0NzE5MjEwLCJpc3MiOiJodHRwczovL2FwZWNsb3VkLWRldi5hdXRoaW5nLmNuL29pZGMiLCJrdWJlYmxvY2tzLmlvL3VpZCI6IjI2NzI3NzcwMjE3NDYyMTY5NiJ9.YwggcY5YQOtM2eMo-zvzv7gvr8DuSL1B6PWlS_HTSScWsr57XM6b7UXPBsErgMzgjyeOlKY9asb4nrujf0AEEn9op3zGM77dyWelJZMvZNSjx8WFNlSpcXc0rtouHlJD2M1Nv3rPPT1eF1dMuX_SMQA4slQ7J9hs4igif2mDsIkuHfTP_rSkU9-DtjnqZKCeiY-3_RlostS5zFrH8sDWwdNvRTjmia3ErRpoR3Z-cpNAgxT5grJ6qn31G25Mh2iSR6m4bUz8golM9vOevX10sAqlnzNTsJvIPVLU3utB43eYophbLXu6Hw2GtVGbYkn5ACVndN0VVZhSsLdBXIqGHA'
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document
class APIDefinition(BaseTool):
    url: str
    method: str
    return_direct = False
    before_need_tool: list = []
    before_prompt: str = "输入有误，请先调用工具：{before_need_tool}，结合回复获取本工具的必要输入参数，然后再调用本工具"
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
        
        before = "输入参数为list格式，需要以逗号分隔，分别代表：{arg_match}，不包括其他无关表达".format(arg_match = str(arg_match))
        after = self.before_prompt.format(before_need_tool = str(self.before_need_tool))
        headers = {'Authorization': f'Bearer {self.bearer_token}'}
        if 'orgName' in arg_match and not input_datas:    
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
                if answer["error"]["code"] == 403:
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
    
    