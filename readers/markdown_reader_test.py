import tempfile
from pathlib import Path

f = "/Users/ziang/git/KubeChat/resources/documents/tos-feishu-parser-markdown/4.8  延迟启动v80s3qlh.md"

from .markdown_reader import MarkdownReader
docs = MarkdownReader().load_data(Path(f))
for doc in docs:
    print(doc.text)

