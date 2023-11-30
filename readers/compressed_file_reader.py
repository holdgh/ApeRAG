from llama_index.schema import Document
from llama_index.readers.base import BaseReader
from pathlib import Path
from typing import Callable, Dict, Generator, List, Optional, Type
import logging

logger = logging.getLogger(__name__)
class CompressedFileReader(BaseReader):

    def load_data(self, file: Path, metadata: Optional[Dict] = None) -> List[Document]:
        return [
            Document(
                text="" ,
                metadata=metadata or {},
            )
        ]



