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

import io
import logging
import mimetypes
from pathlib import Path
from typing import Any, Dict, List, Optional

import pikepdf
import pypdfium2 as pdfium

from aperag.docparser.base import AssetBinPart, MarkdownPart, PdfPart
from aperag.docparser.doc_parser import DocParser
from aperag.objectstore.base import get_object_store

logger = logging.getLogger(__name__)


def is_image_file(suffix_name: str) -> bool:
    return suffix_name.lower() in [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"]


class DocumentParsingResult:
    """Result of document parsing operation"""

    def __init__(self, doc_parts: List[Any], content: str, metadata: Optional[Dict[str, Any]] = None):
        self.doc_parts = doc_parts
        self.content = content
        self.metadata = metadata or {}


class DocumentParser:
    """Document parsing and processing logic"""

    # Configuration constants
    MAX_EXTRACTED_SIZE = 5000 * 1024 * 1024  # 5 GB

    def parse_document(
        self, filepath: str, file_metadata: Dict[str, Any], parser_config: Optional[Dict[str, Any]] = None
    ) -> List[Any]:  # 对文件进行解析分段
        """
        Parse document into parts using DocParser.

        Args:
            filepath: Path to the document file
            file_metadata: Metadata associated with the document
            parser_config: Configuration for the parser  全局配置信息，见setting表【空】

        Returns:
            List of document parts (MarkdownPart, AssetBinPart, etc.)

        Raises:
            ValueError: If the file type is unsupported
        """
        file_metadata = file_metadata or {}
        parser = DocParser(parser_config=parser_config)  # 初始化解析器入口实例【凝聚了当前可用的所有解析器】
        filepath_obj = Path(filepath)

        if not parser.accept(filepath_obj.suffix):  # 检验当前文件扩展名是否支持解析
            raise ValueError(f"unsupported file type: {filepath_obj.suffix}")

        parts = parser.parse_file(filepath_obj, file_metadata)  # TODO 至此~

        # If there are no PdfPart in parts and the doc is a pdf, then add the doc itself as a PdfPart
        if filepath_obj.suffix.lower() == ".pdf":
            if not any(isinstance(p, PdfPart) for p in parts):
                with open(filepath_obj, "rb") as f:
                    parts.append(PdfPart(data=f.read()))

        if is_image_file(filepath_obj.suffix):
            # Convert the image file to an asset
            with open(filepath_obj, "rb") as f:
                image_data = f.read()
                mime_type, _ = mimetypes.guess_type(filepath_obj)
                metadata = file_metadata.copy()
                metadata.update(
                    {
                        "converted_from": "self",
                        "vision_index": True,
                    }
                )
                asset_id = f"file{filepath_obj.suffix}"
                asset_part = AssetBinPart(
                    asset_id=asset_id,
                    data=image_data,
                    metadata=metadata,
                    mime_type=mime_type,
                )
                parts.append(asset_part)
        else:
            # Convert PdfPart to image assets
            pdf_parts = [p for p in parts if isinstance(p, PdfPart)]
            for pdf_part in pdf_parts:
                try:
                    pdf_doc = pdfium.PdfDocument(pdf_part.data)
                    for i, page in enumerate(pdf_doc):
                        # Render page to a PIL image
                        image = page.render(scale=1).to_pil()
                        # Save image to a bytes buffer
                        with io.BytesIO() as buffer:
                            image.save(buffer, format="PNG")
                            image_data = buffer.getvalue()

                        # Create a new AssetBinPart for each page
                        metadata = file_metadata.copy()
                        metadata.update(
                            {
                                "page_idx": i,
                                "converted_from": "pdf",
                                "vision_index": True,
                            }
                        )
                        asset_id = f"page_{i}.png"
                        asset_part = AssetBinPart(
                            asset_id=asset_id,
                            data=image_data,
                            metadata=metadata,
                            mime_type="image/png",
                        )
                        parts.append(asset_part)

                    logger.info(f"Converted {len(pdf_doc)} pages from a PDF part to image assets.")
                except Exception as e:
                    logger.warning(f"Failed to convert PDF part to images: {e}", exc_info=True)

        logger.info(f"Parsed document {filepath} into {len(parts)} parts")
        return parts

    def linearize_pdf(self, data: bytes) -> bytes:
        with pikepdf.open(io.BytesIO(data)) as pdf:
            with io.BytesIO() as buffer:
                pdf.save(buffer, linearize=True)
                return buffer.getvalue()

    def save_processed_content_and_assets(self, doc_parts: List[Any], object_store_base_path: Optional[str]) -> str:  # 将解析后的文本分段，基于对象存储基本路径存入对象存储中
        """
        Save processed content and assets to object storage.

        Args:
            doc_parts: List of document parts from DocParser
            object_store_base_path: Base path for object storage, if None, skip saving  基本路径规则：“user-{用户id}/{知识库id}/{文档信息id}”

        Returns:
            Full markdown content of the document

        Raises:
            Exception: If object storage operations fail
        """

        content = ""
        # -- 处理分段中的markdown类型的第一个和pdf类型的第一个元素 TODO 这里处理的目的是什么呢？【推测：要想明确这里的保存逻辑，需要知道此前的文档解析分段逻辑，猜测是将文档解析为一个markdown格式，一个pdf格式和asserts【猜测是具体的文本分段】】
        # Extract full markdown content if available
        md_part = next((part for part in doc_parts if isinstance(part, MarkdownPart)), None)  # 从doc_parts列表中查找第一个MarkdownPart类型的元素，并将其赋值给md_part；如果找不到，则md_part为None。
        if md_part is not None:
            content = md_part.markdown
            doc_parts.remove(md_part)  # 这里删除的目的是已经处理当前分段，后续不在进行判断处理

        pdf_part = next((part for part in doc_parts if isinstance(part, PdfPart)), None)  # 从doc_parts列表中查找第一个PdfPart类型的元素，并将其赋值给pdf_part；如果找不到，则pdf_part为None。
        if pdf_part is not None:
            doc_parts.remove(pdf_part)  # 这里删除的目的是什么呢？
        # 基本路径非空时，保存至对象存储
        # Save to object storage if base path is provided
        if object_store_base_path is not None:
            base_path = object_store_base_path
            obj_store = get_object_store()  # 获取对象存储实例【aperag.objectstore.local.Local】
            # -- 保存分段中的第一个markdown内容到“{对象存储根路径}/user-{用户id}/{知识库id}/{文档信息id}/parsed.md”
            # Save markdown content
            md_upload_path = f"{base_path}/parsed.md"
            md_data = content.encode("utf-8")
            obj_store.put(md_upload_path, md_data)  # 文件路径，文件内容
            logger.info(f"uploaded markdown content to {md_upload_path}, size: {len(md_data)}")
            # -- 保存分段中的第一个pdf到“{对象存储根路径}/user-{用户id}/{知识库id}/{文档信息id}/converted.pdf”
            if pdf_part is not None:
                converted_pdf_upload_path = f"{base_path}/converted.pdf"
                linearized_pdf_data = self.linearize_pdf(pdf_part.data)
                obj_store.put(converted_pdf_upload_path, linearized_pdf_data)  # 文件路径，文件内容
                logger.info(f"uploaded converted pdf to {converted_pdf_upload_path}, size: {len(linearized_pdf_data)}")
            # -- 保存数据资产？
            # Save assets
            to_be_deleted = []
            asset_count = 0
            for part in doc_parts:
                if not isinstance(part, AssetBinPart):  # 过滤掉非资产
                    continue
                if not part.metadata.get("vision_index"):  # 收集视觉数据到to_be_deleted
                    to_be_deleted.append(part)

                asset_upload_path = f"{base_path}/assets/{part.asset_id}"
                obj_store.put(asset_upload_path, part.data)  # 保存数据资产到“{对象存储根路径}/user-{用户id}/{知识库id}/{文档信息id}/assets/{part.asset_id}”
                asset_count += 1
                logger.info(f"uploaded asset to {asset_upload_path}, size: {len(part.data)}")
            # 删除视觉数据？
            if to_be_deleted:
                for part in to_be_deleted:
                    doc_parts.remove(part)

            logger.info(f"Saved {asset_count} assets to object storage")
        # 返回markdown内容
        return content

    def extract_content_from_parts(self, doc_parts: List[Any]) -> str:
        """
        Extract content from document parts when no MarkdownPart is available.

        Args:
            doc_parts: List of document parts

        Returns:
            Concatenated content from all text parts
        """
        from aperag.docparser.base import MarkdownPart

        # Check if MarkdownPart exists
        md_part = next((part for part in doc_parts if isinstance(part, MarkdownPart)), None)
        if md_part is not None:
            return md_part.markdown

        # If no MarkdownPart, concatenate content from other parts
        content_parts = []
        for part in doc_parts:
            if hasattr(part, "content") and part.content:
                content_parts.append(part.content)

        return "\n\n".join(content_parts)

    def process_document_parsing(
        self,
        filepath: str,
        file_metadata: Dict[str, Any],
        object_store_base_path: Optional[str] = None,
        parser_config: Optional[Dict[str, Any]] = None,  # 全局配置信息，见setting表【空】
    ) -> DocumentParsingResult:  # 文件解析和分段处理
        """
        Complete document parsing workflow

        Args:
            filepath: Path to the document file
            file_metadata: Metadata associated with the document
            object_store_base_path: Base path for object storage
            parser_config: Configuration for the parser

        Returns:
            DocumentParsingResult containing parsed parts and content
        """
        try:
            # -- 将文件解析为分段
            # Parse document into parts
            doc_parts = self.parse_document(filepath, file_metadata, parser_config)
            # -- 将文件分段保存至对象存储
            # Save processed content and assets to object storage
            content = self.save_processed_content_and_assets(doc_parts, object_store_base_path)  # 将解析后的文本分段，基于对象存储基本路径存入对象存储中

            return DocumentParsingResult(doc_parts=doc_parts, content=content, metadata={"parts_count": len(doc_parts)})

        except Exception as e:
            raise Exception(f"Document parsing failed for {filepath}: {str(e)}")


# Global parser instance
document_parser = DocumentParser()
