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

# Configuration constants
import json
from typing import Any, List, Tuple

from aperag.exceptions import CollectionNotFoundException, DocumentNotFoundException


class TaskConfig:
    RETRY_COUNTDOWN_COLLECTION = 60
    RETRY_MAX_RETRIES_COLLECTION = 2


def parse_document_content(document, collection) -> Tuple[str, List[Any], Any]:  # 解析文档【该操作可被所有类型的索引任务共用】
    """Parse document content for indexing (shared across all index types)"""
    from aperag.index.document_parser import document_parser
    from aperag.schema.utils import parseCollectionConfig
    from aperag.service.setting_service import setting_service
    from aperag.source.base import get_source

    # Get document source and prepare local file
    # -- 解析知识库配置信息，并根据其中的source字段获取文件source实例
    source = get_source(parseCollectionConfig(collection.config))
    # -- 基于文档信息，使用文件source实例获取LocalDocument实例
    metadata = json.loads(document.doc_metadata or "{}")
    metadata["doc_id"] = document.id
    local_doc = source.prepare_document(name=document.name, metadata=metadata)

    try:
        # -- 基于全局配置信息，对文件进行解析和分段
        global_settings = setting_service.get_all_settings_sync()  # 查询setting表全量信息

        # Parse document to get content and parts
        parsing_result = document_parser.process_document_parsing(
            local_doc.path,
            local_doc.metadata,
            document.object_store_base_path(),  # 为当前文档信息实例生成对象存储基本路径，基本路径规则：“user-{用户id}/{知识库id}/{文档信息id}”
            global_settings,
        )
        # -- 如果文件是在对话过程中上传的，则为每个分段设置元数据【对话id和文件id】
        # Add chat metadata to all document parts if this is a chat upload
        doc_parts = parsing_result.doc_parts
        if document.doc_metadata:
            try:
                doc_metadata = json.loads(document.doc_metadata)
                if doc_metadata.get("file_type") == "chat_upload":
                    chat_id = doc_metadata.get("chat_id")
                    if chat_id:
                        for part in doc_parts:
                            if hasattr(part, "metadata"):
                                if part.metadata is None:
                                    part.metadata = {}
                                part.metadata["chat_id"] = chat_id
                                part.metadata["document_id"] = document.id
                            else:
                                # Create metadata if it doesn't exist
                                part.metadata = {"chat_id": chat_id, "document_id": document.id}
            except json.JSONDecodeError:
                pass

        return parsing_result.content, doc_parts, local_doc
    except Exception as e:
        # Cleanup on error
        source.cleanup_document(local_doc.path)
        raise e


def cleanup_local_document(local_doc, collection):
    """Cleanup local document after processing"""
    from aperag.schema.utils import parseCollectionConfig
    from aperag.source.base import get_source

    source = get_source(parseCollectionConfig(collection.config))
    source.cleanup_document(local_doc.path)


def get_document_and_collection(document_id: str, ignore_deleted: bool = True):
    """Get document and collection objects"""
    from aperag.db.ops import db_ops

    document = db_ops.query_document_by_id(document_id, ignore_deleted)
    if not document:
        raise DocumentNotFoundException(document_id)

    collection = db_ops.query_collection_by_id(document.collection_id, ignore_deleted)
    if not collection:
        raise CollectionNotFoundException(document.collection_id)

    return document, collection
