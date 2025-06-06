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
from typing import Any, List

from langchain_core.embeddings import Embeddings
from llama_index.core.schema import BaseNode, TextNode

from aperag.docparser.base import Part
from aperag.docparser.chunking import rechunk
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
    Handles embedding for documents from parsed parts.

    This class takes pre-parsed document parts, chunks the content, generates embeddings,
    and stores the nodes in the vector database.
    """

    def __init__(
        self,
        *,
        parts: List[Part],
        vector_store_adaptor: VectorStoreConnectorAdaptor,
        embedding_model: Embeddings = None,
        vector_size: int = None,
        **kwargs: Any,
    ) -> None:
        # 1. Initialize the base class with vector store and embedding details
        super().__init__(vector_store_adaptor, embedding_model, vector_size)

        # 2. Store document parts
        self.parts = parts

        # 3. Initialize chunking parameters
        self.chunk_size = kwargs.get("chunk_size", settings.CHUNK_SIZE)
        self.chunk_overlap = kwargs.get("chunk_overlap", settings.CHUNK_OVERLAP_SIZE)
        self.tokenizer = get_default_tokenizer()

    def load_data(self, **kwargs) -> List[str]:
        """
        Processes document parts, rechunks content, generates embeddings,
        and stores nodes in the vector database.

        Returns:
            List[str]: A list of vector store IDs
        """
        nodes: List[BaseNode] = []

        # 1. Get document parts
        doc_parts = self.parts
        if len(doc_parts) == 0:
            return []

        # 2. Rechunk the document parts (resulting in text parts)
        # After rechunk(), parts only contains TextPart
        parts = rechunk(doc_parts, self.chunk_size, self.chunk_overlap, self.tokenizer)

        # 3. Process each text chunk
        for part in parts:
            if not part.content:
                continue

            # 3.1 Prepare metadata paddings (titles, labels)
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
                logger.debug("add extra prefix for document before embedding: %s", prefix)

            # 3.2 Construct text for embedding with paddings
            if prefix:
                text = f"{prefix}\n\n{part.content}"
            else:
                text = part.content
            # 3.3 Prepare metadata for the node
            metadata = part.metadata.copy()
            metadata["source"] = metadata.get("name", "")
            # 3.4 Create TextNode
            nodes.append(TextNode(text=text, metadata=metadata))

        # 4. Generate embeddings for text chunks
        texts = [node.get_content() for node in nodes]
        vectors = self.embedding.embed_documents(texts)
        # 5. Assign embeddings to nodes
        for i in range(len(vectors)):
            nodes[i].embedding = vectors[i]

        logger.info(f"processed document with {len(doc_parts)} parts and {len(vectors)} chunks")
        # 6. Add nodes to vector store and return results
        return self.connector.store.add(nodes)

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
