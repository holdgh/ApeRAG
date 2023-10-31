from pathlib import Path
from typing import Dict, List, Optional

from llama_index.readers.base import BaseReader
from llama_index.schema import Document
from unstructured.chunking.title import chunk_by_title

from unstructured.partition.docx import partition_docx

CHUNK_SPLIT_THRESHOLD = 500


class MyDocxReader(BaseReader):
    """Docx parser."""

    def load_data(
            self, file: Path, extra_info: Optional[Dict] = None
    ) -> List[Document]:
        elements = partition_docx(str(file))
        total_size = 0
        for e in elements:
            total_size += len(e.to_dict()["text"])
        chunks = chunk_by_title(elements, new_after_n_chars=int(min(total_size / 3, CHUNK_SPLIT_THRESHOLD)))
        res = []
        for chunk in chunks:
            res.append(Document(text=chunk.to_dict()["text"], metadata=chunk.metadata.to_dict()))
        return res
