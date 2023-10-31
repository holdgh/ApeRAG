import logging

from pathlib import Path
from typing import Dict, List, Optional
from llama_index.readers.base import BaseReader
from llama_index.schema import Document
from unstructured.chunking.title import chunk_by_title
from unstructured.partition.doc import partition_doc

logger = logging.getLogger(__name__)

CHUNK_SPLIT_THRESHOLD = 500


class MyDocReader(BaseReader):
    """Doc Parser."""
    """
    Convert the 'doc' type to 'docx' using 'win32com,' and then parse it using the 'docx' type
    """

    def load_data(self, file: Path, metadata: Optional[Dict] = None) -> List[Document]:
        elements = partition_doc(str(file))
        total_size = 0
        for e in elements:
            total_size += len(e.to_dict()["text"])
        chunks = chunk_by_title(elements, new_after_n_chars=int(min(total_size / 3, CHUNK_SPLIT_THRESHOLD)))
        res = []
        for chunk in chunks:
            res.append(Document(text=chunk.to_dict()["text"], metadata=chunk.metadata.to_dict()))
        return res
