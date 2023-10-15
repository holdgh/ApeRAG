import asyncio

import openai

token = "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"


async def request(prompt):
    response = openai.ChatCompletion.create(
        api_key=token,
        api_base="http://3.113.33.124:3000/proxy/v1",
        stream=True,
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}])
    for chunk in response:
        choices = chunk["choices"]
        if len(choices) > 0:
            choice = choices[0]
            if choice["finish_reason"] == "stop":
                return
            content = choice["delta"]["content"]
            yield content


async def main():
    async for tokens in request("请介绍一下k8s"):
        print(tokens, end="")

if __name__ == "__main__":
    asyncio.run(main())
