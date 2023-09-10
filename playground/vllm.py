import json
from typing import Dict, Any

import requests

from kubechat.llm.predict import CustomLLMPredictor


def generate_stream(
        prompt,
        **kwargs: Any,
) -> str:
    input = {
        "prompt": prompt,
        "use_beam_search": False,
        "n": 1,
        "temperature": 0,
        "stream": True,
        "max_tokens": 4096,
    }
    response = requests.post("%s/generate" % kwargs["endpoint"], json=input, stream=True)
    output = ""
    for chunk in response.iter_lines(chunk_size=2048, decode_unicode=False, delimiter=b"\0"):
        if chunk:
            data = json.loads(chunk.decode("utf-8"))
            tokens = data["text"][0][len(output):]
            yield tokens
            output = data["text"][0]


def generate(prompt, **kwargs: Any) -> str:
    input = {
        "prompt": prompt,
        "use_beam_search": False,
        "n": 1,
        "temperature": 0,
        "max_tokens": 4096,
    }
    response = requests.post("%s/generate" % kwargs["endpoint"], json=input)
    data = json.loads(response.text)
    return data["text"][0]


predictor = CustomLLMPredictor()
for token in predictor.generate_stream("请写一首五言绝句"):
    print(token, end="")

# for token in generate("请写一首五言绝句", endpoint="http://localhost:8080"):
#     print(token, end="")
