from typing import Dict, Type

from llama_index.readers.base import BaseReader
from llama_index.readers.file.docs_reader import  PDFReader
from llama_index.readers.file.ipynb_reader import IPYNBReader
from llama_index.readers.file.mbox_reader import MboxReader
from llama_index.readers.file.tabular_reader import PandasCSVReader
from llama_index.readers.file.video_audio_reader import VideoAudioReader

from readers.compose_image_reader import ComposeImageReader
from readers.docx_reader import MyDocxReader
from readers.epub_reader import EpubReader
from readers.markdown_reader import MarkdownReader
from readers.pptx_reader import PptxReader

DEFAULT_FILE_READER_CLS: Dict[str, Type[BaseReader]] = {
    ".pdf": PDFReader,
    # ".docx": DocxReader,
    ".docx": MyDocxReader,
    ".pptx": PptxReader,
    ".jpg": ComposeImageReader,
    ".png": ComposeImageReader,
    ".jpeg": ComposeImageReader,
    ".mp3": VideoAudioReader,
    ".mp4": VideoAudioReader,
    ".csv": PandasCSVReader,
    ".epub": EpubReader,
    ".md": MarkdownReader,
    ".mbox": MboxReader,
    ".ipynb": IPYNBReader,
    ".txt": MarkdownReader,
}
