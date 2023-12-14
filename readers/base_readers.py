from typing import Dict, Type

from llama_index.readers.base import BaseReader
from llama_index.readers.file.docs_reader import PDFReader, DocxReader
from llama_index.readers.file.ipynb_reader import IPYNBReader
from llama_index.readers.file.mbox_reader import MboxReader
from llama_index.readers.file.tabular_reader import PandasCSVReader
from llama_index.readers.file.video_audio_reader import VideoAudioReader

from readers.compose_image_reader import ComposeImageReader
from readers.doc_reader import MyDocReader
from readers.docx_reader import MyDocxReader
from readers.epub_reader import EpubReader
from readers.markdown_reader import MarkdownReader
from readers.pptx_reader import PptxReader
from readers.compose_audio_reader import ComposeAudioReader
from readers.compressed_file_reader import  CompressedFileReader
from readers.excel_reader import ExcelReader
from readers.ppt_reader import PptReader
from readers.html_reader import HtmlReader


DEFAULT_FILE_READER_CLS: Dict[str, Type[BaseReader]] = {
    ".pdf": PDFReader,
    ".docx": DocxReader,
    # ".docx": MyDocxReader,
    ".doc": MyDocReader,
    ".pptx": PptxReader,
    ".ppt":PptReader,
    ".html":HtmlReader,
    ".xlxs":ExcelReader,
    ".jpg": ComposeImageReader,
    ".png": ComposeImageReader,
    ".jpeg": ComposeImageReader,
    ".mp3": ComposeAudioReader,
    ".mp4": ComposeAudioReader,
    ".mpeg": ComposeAudioReader,
    ".mpga": ComposeAudioReader,
    ".m4a": ComposeAudioReader,
    ".wav": ComposeAudioReader,
    ".webm": ComposeAudioReader,
    ".csv": PandasCSVReader,
    ".epub": EpubReader,
    ".md": MarkdownReader,
    ".mbox": MboxReader,
    ".ipynb": IPYNBReader,
    ".txt": MarkdownReader,
    ".zip": CompressedFileReader,
    ".rar": CompressedFileReader,
    ".7z": CompressedFileReader,
    ".tar": CompressedFileReader,
    ".gz": CompressedFileReader,
    ".xz": CompressedFileReader,
    ".bz2": CompressedFileReader,
    ".tar.gz": CompressedFileReader,
    ".tar.xz": CompressedFileReader,
    ".tar.bz2": CompressedFileReader,
    ".tar.7z": CompressedFileReader
}


FULLTEXT_SUFFIX = {
    ".md": True,
    ".txt": True,
}


SUPPORTED_COMPRESSED_EXTENSIONS=['.zip','.rar', '.r00','.7z','.tar', '.gz', '.xz', '.bz2', '.tar.gz', '.tar.xz', '.tar.bz2', '.tar.7z']

