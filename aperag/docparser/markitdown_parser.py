# Copyright 2025 ApeCloud, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import tempfile
from pathlib import Path
from typing import Any

from markitdown import MarkItDown

from aperag.docparser.base import BaseParser, FallbackError, Part
from aperag.docparser.parse_md import parse_md
from aperag.docparser.utils import convert_office_doc, get_soffice_cmd

SUPPORTED_EXTENSIONS = [
    ".txt",
    ".text",
    ".md",
    ".markdown",
    ".html",
    ".htm",
    ".ipynb",
    ".pdf",
    ".docx",
    ".doc",  # convert to .docx first
    ".xlsx",
    ".xls",
    ".pptx",
    ".ppt",  # convert to .pptx first
    ".epub",
]


class MarkItDownParser(BaseParser):  # 常见文档解析器
    name = "markitdown"

    def supported_extensions(self) -> list[str]:
        return SUPPORTED_EXTENSIONS

    def parse_file(self, path: Path, metadata: dict[str, Any] = {}, **kwargs) -> list[Part]:  # 【对于doc和ppt进行office文件格式转化】解析文件
        extension = path.suffix.lower()  # 获取当前文件的扩展名
        target_format = None
        if extension == ".doc":
            target_format = ".docx"
        elif extension == ".ppt":
            target_format = ".pptx"
        if target_format:  # 如果为doc或ppt格式的文件，则将其转化为office格式文档docx或pptx，然后对相应office文档进行解析
            if get_soffice_cmd() is None:  # 查找系统中是否安装了 soffice 程序及其可执行文件路径，用于进行office文件转换
                raise FallbackError("soffice command not found")
            with tempfile.TemporaryDirectory() as temp_dir:
                converted = convert_office_doc(path, Path(temp_dir), target_format)
                return self._parse_file(converted, metadata, **kwargs)
        return self._parse_file(path, metadata, **kwargs)

    def _parse_file(self, path: Path, metadata: dict[str, Any] = {}, **kwargs) -> list[Part]:  # 解析文件
        """
        MarkItDown 是微软 AutoGen 团队开发的轻量级 Python 工具，专为大语言模型设计，在 RAG 系统中具有诸多特点：

        支持多种文件格式：能够将 20 多种文件格式转换为 Markdown 格式，包括 PDF、PPT、Word、Excel、图像、音频、HTML、CSV、JSON、XML、ZIP、EPub 等，还支持 YouTube 视频链接，可提取字幕。
        保留文档结构：在转换过程中，能完美保留文档的层次结构，如标题层级、列表格式、表格结构、超链接、图像引用、文本格式（如粗体、斜体）等，为后续的语义理解和检索提供了丰富的上下文信息。
        内容清洁与优化：自动过滤样式信息，提取纯净的语义内容，生成的 Markdown 文本特别适合向量化和语义检索，有助于提高 RAG 系统的检索效果。
        轻量高效：设计轻量级，易于集成到现有脚本和工作流程中，不会产生不必要的开销，能够高效地处理文档转换任务，提升 RAG 系统的整体性能。
        集成 LLM 能力：可以选择使用 LLM 来增强转换效果，例如利用 LLM 为文档中的图像生成描述，还可作为 MCP 服务器与 Claude Desktop 之类的 LLM 应用程序无缝集成。
        提供多种使用方式：提供了简单易用的命令行界面，方便在终端中进行文件转换操作，同时也有灵活的 Python API，便于集成到其他 Python 应用中，还支持 Docker 运行，方便在不同环境中部署。
        插件系统扩展：采用插件系统，允许开发者根据需求扩展功能，可通过安装特定插件来添加对新格式或转换逻辑的支持，具有很强的扩展性和灵活性。

        """
        # -- 将文件转为markdown格式
        mid = MarkItDown()  # 第三方依赖库MarkItDown
        result = mid.convert_local(path, keep_data_uris=True)
        # -- 对markdown文件进行解析分段
        return parse_md(result.markdown, metadata)
