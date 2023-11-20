from llama_index.schema import Document
from llama_index.readers.base import BaseReader
from pathlib import Path
from typing import Callable, Dict, Generator, List, Optional, Type
import logging

logger = logging.getLogger(__name__)
class CompressedFileReader(BaseReader):

    def __init__(
            self,
            file_extractor: Optional[Dict[str, BaseReader]] = None,
            num_files_limit: Optional[int] = None,
            file_metadata: Optional[Callable[[str], Dict]] = None,
    ) -> None:
        """Initialize with parameters."""
        super().__init__(
            file_extractor,
            num_files_limit,
            file_metadata,
        )

    def load_data(self, file: Path, metadata: Optional[Dict] = None) -> List[Document]:
        return [
            Document(
                text="" ,
                metadata=metadata or {},
            )
        ]



