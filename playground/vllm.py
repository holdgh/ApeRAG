import json
from typing import Dict, Any

import requests

from kubechat.llm.predict import CustomLLMPredictor, KubeBlocksLLMPredictor

endpoint = "http://a4bc866e82e334dbc8f18534ec3c6e49-a0be02f868125b84.elb.ap-northeast-1.amazonaws.com:8080"

# predictor = CustomLLMPredictor()
# for token in predictor.generate_stream("请写一首五言绝句"):
#     print(token, end="")

prompts = [
    "我给你起个名字，你要记住，你叫大大大模型",
    "你叫什么名字"
]

predictor = KubeBlocksLLMPredictor(endpoint=endpoint)

for prompt in prompts:
    for token in predictor.generate_stream(prompt):
        print(token, end="")
    print("\n--------------\n")
