#!/usr/bin/env python3
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

# -*- coding: utf-8 -*-
import faulthandler
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Tuple

from langchain_core.embeddings import Embeddings
from llama_index.core.schema import BaseNode, TextNode

from aperag.docparser.base import AssetBinPart, MarkdownPart, Part
from aperag.docparser.chunking import rechunk
from aperag.docparser.doc_parser import DocParser
from aperag.objectstore.base import get_object_store
from aperag.utils.tokenizer import get_default_tokenizer
from aperag.vectorstore.connector import VectorStoreConnectorAdaptor
from config import settings

logger = logging.getLogger(__name__)

faulthandler.enable()


class DocumentBaseEmbedding(ABC):
    def __init__(
        self,
        vector_store_adaptor: VectorStoreConnectorAdaptor,
        embedding_model: Embeddings = None,
        vector_size: int = None,
        **kwargs: Any,
    ) -> None:
        self.connector = vector_store_adaptor.connector
        # Improved logic to handle optional embedding_model/vector_size
        if embedding_model is None or vector_size is None:
            raise ValueError("lacks embedding model or vector size")

        self.embedding, self.vector_size = embedding_model, vector_size
        self.client = vector_store_adaptor.connector.client

    @abstractmethod
    def load_data(self, **kwargs: Any):
        pass


class LocalPathEmbedding(DocumentBaseEmbedding):
    """
    Handles embedding for documents located at a local file path.

    This class parses a local document, chunks its content, generates embeddings,
    and stores the processed data and assets.
    """

    def __init__(
        self,
        *,
        filepath: str,
        file_metadata: Dict[str, Any],
        object_store_base_path: str | None = None,
        vector_store_adaptor: VectorStoreConnectorAdaptor,
        embedding_model: Embeddings = None,
        vector_size: int = None,
        **kwargs: Any,
    ) -> None:
        # 1. Initialize the base class with vector store and embedding details
        super().__init__(vector_store_adaptor, embedding_model, vector_size)

        # 2. Store document-specific attributes
        self.filepath = filepath
        self.file_metadata = file_metadata or {}
        self.object_store_base_path = object_store_base_path
        # 3. Initialize document parser and chunking parameters
        self.parser = DocParser()  # TODO: use the parser config from the collection
        self.chunk_size = kwargs.get("chunk_size", settings.CHUNK_SIZE)
        self.chunk_overlap = kwargs.get("chunk_overlap", settings.CHUNK_OVERLAP_SIZE)
        self.tokenizer = get_default_tokenizer()

    def parse_doc(
        self,
    ) -> list[Part]:
        """
        Parses the document at the given filepath.

        Returns:
            list[Part]: A list of document parts.
        Raises:
            ValueError: If the file type is unsupported.
        """
        filepath = Path(self.filepath)
        if not self.parser.accept(filepath.suffix):
            raise ValueError(f"unsupported file type: {filepath.suffix}")
        parts = self.parser.parse_file(filepath, self.file_metadata)
        return parts

    def load_data(self, **kwargs) -> Tuple[List[str], str]:
        """
        Loads, processes, embeds, and stores data from the document.

        Processes includes parsing, chunking, adding metadata paddings.
        Stores markdown content and assets to object storage.
        Embeds text chunks and stores nodes in the vector database.

        Returns:
            Tuple[List[str], str]: A tuple containing a list of vector store IDs
                                   and the full markdown content of the document.
        """
        nodes: List[BaseNode] = []
        content = ""

        # 1. Parse the document into parts
        doc_parts = self.parse_doc()
        if len(doc_parts) == 0:
            return [], ""

        # 2. Rechunk the document parts (resulting in text parts)
        # After rechunk(), parts only contains TextPart
        parts = rechunk(doc_parts, self.chunk_size, self.chunk_overlap, self.tokenizer)

        # 3. Extract full markdown content if available
        md_part = next((part for part in doc_parts if isinstance(part, MarkdownPart)), None)
        if md_part is not None:
            content = md_part.markdown

        # 4. Process each text chunk
        for part in parts:
            if not part.content:
                continue

            # Append chunk content to full content if markdown part not found
            if md_part is None:
                content += part.content + "\n\n"

            # 4.1 Prepare metadata paddings (titles, labels)
            paddings = []
            # padding titles of the hierarchy
            if "titles" in part.metadata:
                paddings.append("Breadcrumbs: " + " > ".join(part.metadata["titles"]))

            # padding user custom labels
            if "labels" in part.metadata:
                labels = []
                for item in part.metadata.get("labels", [{}]):
                    if not item.get("key", None) or not item.get("value", None):
                        continue
                    labels.append("%s=%s" % (item["key"], item["value"]))
                paddings.append(" ".join(labels))

            prefix = ""
            if len(paddings) > 0:
                prefix = "\n\n".join(paddings)
                logger.debug("add extra prefix for document %s before embedding: %s", self.filepath, prefix)

            # embedding without the prefix #, which is usually used for padding in the LLM
            # lines = []
            # for line in text.split("\n"):
            #     lines.append(line.strip("#").strip())
            # text = "\n".join(lines)

            # embedding without the code block
            # text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)

            # 4.2 Construct text for embedding with paddings
            if prefix:
                text = f"{prefix}\n\n{part.content}"
            else:
                text = part.content
            # 4.3 Prepare metadata for the node
            metadata = part.metadata.copy()
            metadata["source"] = metadata.get("name", "")
            # 4.4 Create TextNode
            nodes.append(TextNode(text=text, metadata=metadata))

        # 5. Save processed content and assets to object storage if base path is provided
        if self.object_store_base_path is not None:
            base_path = self.object_store_base_path
            obj_store = get_object_store()

            # 5.1 Save markdown content
            md_upload_path = f"{base_path}/parsed.md"
            md_data = content.encode("utf-8")
            obj_store.put(md_upload_path, md_data)
            logger.info(f"uploaded markdown content to {md_upload_path}, size: {len(md_data)}")

            # 5.2 Save assets
            for part in doc_parts:
                if not isinstance(part, AssetBinPart):
                    continue
                asset_upload_path = f"{base_path}/assets/{part.asset_id}"
                obj_store.put(asset_upload_path, part.data)
                logger.info(f"uploaded asset to {asset_upload_path}, size: {len(part.data)}")

        # 6. Generate embeddings for text chunks
        texts = [node.get_content() for node in nodes]
        vectors = self.embedding.embed_documents(texts)
        # 7. Assign embeddings to nodes
        for i in range(len(vectors)):
            nodes[i].embedding = vectors[i]

        logger.info(f"processed file: {self.filepath} with {len(vectors)} chunks")
        # 8. Add nodes to vector store and return results
        return self.connector.store.add(nodes), content

    def delete(self, **kwargs) -> bool:
        """
        Deletes the document's data from the vector store.

        Args:
            **kwargs: Keyword arguments passed to the connector's delete method.

        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        # Delegate deletion to the vector store connector
        return self.connector.delete(**kwargs)
