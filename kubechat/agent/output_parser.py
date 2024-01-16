from langchain.schema import AgentAction, AgentFinish
from langchain.agents import AgentExecutor, AgentOutputParser
from langchain.output_parsers.json import parse_json_markdown
from typing import Dict, Union, Any, List
import re
from prompt import FORMAT_INSTRUCTIONS_CHINESE

class CustomOutputParser(AgentOutputParser):

    def get_format_instructions(self) -> str:
        return FORMAT_INSTRUCTIONS_CHINESE

    def parse(self, text: str) -> Union[AgentAction, AgentFinish]:
        cleaned_output = text.strip()
        cleaned_output = text.replace("\n","")
        try:
            response = parse_json_markdown(text)
            action_value = response.get("action","")
            action_input_value = str(response.get("action_input",""))
            if action_value == "Final Answer":
                return AgentFinish({"output": action_input_value}, text)
            else:
                return AgentAction(action_value, action_input_value, text)
        except:
            # 定义匹配正则
            action_pattern = r'"action"\s*:\s*"([^"]*)"'
            action_input_pattern =  r'input"\s*:\s*\[([^\]]*)\]'
            # 提取出匹配到的action值
            action = re.search(action_pattern, cleaned_output)
            action_input = re.search(action_input_pattern, cleaned_output)
            if action:
                action_value = action.group(1)
            else:
                action_value = ""
            if action_input:
                action_input_value = action_input.group(1)
            else:
                action_input_pattern = r'input"\s*:\s*"([^"]*)"'
                action_input = re.search(action_input_pattern, cleaned_output)
                action_input_value = action_input.group(1) if action_input else ""
            
            
            # 如果遇到'Final Answer'，则判断为本次提问的最终答案
            if action_value and action_input_value:
                if action_value == "Final Answer" or action_value == "":
                    return AgentFinish({"output": action_input_value}, text)
                else:
                    return AgentAction(action_value, action_input_value, text)
