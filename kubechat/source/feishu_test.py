import os

from kubechat.source.utils import FeishuClient, Feishu2Markdown

ctx = {
    "app_id": os.environ.get("APP_ID"),
    "app_secret": os.environ.get("APP_SECRET"),
}

node_id = "GnDvdxaSRoBllOxyucWcrEuincg"

client = FeishuClient(ctx)
blocks = client.get_docx_blocks(node_id)
content = Feishu2Markdown(node_id, blocks).gen()
print(content)
