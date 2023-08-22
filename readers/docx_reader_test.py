import tempfile
from pathlib import Path

from docx_reader import MyDocxReader

test_my_docx_reader = MyDocxReader()

res = test_my_docx_reader.load_data(Path("/Users/alal/KubeChat/tests/reader_test/docx_reader/KubeBlocks overview.docx"))

print(res)
