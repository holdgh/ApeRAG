import os
from openai import OpenAI

bot_id = "botbd4e7f1f51587e96"

client = OpenAI(
    # This is the default and can be omitted
    base_url="http://localhost:8000/v1",
    api_key="sk-aae658f87e5149acb6f8c08220de75f7",
)

stream = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "developer", "content": "Talk like a database expert."},
        {
            "role": "user",
            "content": "how to create starrocks cluster using kbcli?",
        },
    ],
    stream=True,
    extra_query={"bot_id": bot_id}
)

for chunk in stream:
    if chunk.choices:
        print(chunk.choices[0].delta.content or "", end="")