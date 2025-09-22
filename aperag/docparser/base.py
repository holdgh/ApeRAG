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

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class FallbackError(Exception):  # 自定义回调异常，用以处理依赖服务【比如docrag文件解析服务】不可用的异常处理
    pass


class Part(BaseModel):  # 文件基类定义
    content: str | None = Field(
        default=None,
        description="The parsed content. If None, it means that information extraction has not been performed on this node yet.",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class MarkdownPart(Part):  # markdown文件定义
    markdown: str


class PdfPart(Part):  # 仅支持docray\mineru，但目前docray\mineru服务不可用，因此文档解析不会主动产生pdf文件实例
    data: bytes


class TextPart(Part):
    pass


class TitlePart(TextPart):
    level: int


class CodePart(Part):
    lang: str | None = None


class MediaPart(Part):
    url: str
    mime_type: str | None = None


class ImagePart(MediaPart):
    alt_text: str | None = None
    title: str | None = None


class AssetBinPart(Part):  # 由于当前mineru服务不可用，当前可形成AssetBinPart实例的地方主要在aperag.docparser.parse_md.extract_data_uri【由图片资源创建资产实例】和aperag.index.document_parser.DocumentParser.parse_document【将图片文件和pdf文件【每页】转化为资产实例】
    asset_id: str
    data: bytes
    mime_type: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)  # pdf实例也转化为图片资源、当前文件为图片时也转化为图片资源，这两种情况AssetBinPart的元数据视觉标记为True


class BaseParser(ABC):  # 抽象类型文件解析器定义
    def __init__(self, **kwargs):
        pass

    @abstractmethod
    def supported_extensions(self) -> list[str]: ...

    def accept(self, extension: str) -> bool:
        return extension.lower() in self.supported_extensions()

    @abstractmethod
    def parse_file(self, path: Path, metadata: dict[str, Any] = {}, **kwargs) -> list[Part]: ...
