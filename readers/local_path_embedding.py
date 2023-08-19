#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import logging
import os.path
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional

from llama_index import (
    LangchainEmbedding,
)
from llama_index.data_structs.data_structs import Node
from llama_index.embeddings import base, openai
from llama_index.schema import NodeRelationship, RelatedNodeInfo
from llama_index.vector_stores import qdrant
from llama_index.vector_stores.types import NodeWithEmbedding

from kubechat.source.base import Source
from readers.base_embedding import DocumentBaseEmbedding
from readers.local_path_reader import InteractiveSimpleDirectoryReader
from vectorstore.connector import VectorStoreConnectorAdaptor


logger = logging.getLogger(__name__)


class LocalPathEmbedding(DocumentBaseEmbedding):
    def __init__(
        self,
        vector_store_adaptor: VectorStoreConnectorAdaptor,
        embedding_model: LangchainEmbedding = None,
        vector_size: int = 0,
        **kwargs: Any,
    ) -> None:
        uri_path = kwargs.get("input_files") or kwargs.get("input_dir")
        super().__init__(uri_path, vector_store_adaptor, embedding_model, vector_size)

        self.args = kwargs
        self.reader = InteractiveSimpleDirectoryReader(**kwargs)

    def load_data(self) -> list[str]:
        end = False
        embedding = self.embedding
        count = 0

        while not end:
            docs, file_name = self.reader.load_data()
            if not docs:
                end = True
                break

            nodes: List[NodeWithEmbedding] = []
            prefix = "\n\n".join([f"{k}: {v}" for k, v in Source.get_metadata(file_name).items()])
            for doc in docs:
                text = f"{prefix}\n{doc.text}"
                vector = embedding.get_text_embedding(text)
                doc.embedding = vector
                node = Node(
                    text=text,
                    doc_id=doc.doc_id,
                )
                node.relationships = {
                    NodeRelationship.SOURCE: RelatedNodeInfo(
                        node_id=node.node_id, metadata={"source": f"{file_name}"}
                    )
                }
                nodes.append(NodeWithEmbedding(node=node, embedding=vector))
            count = count + 1
            print(f"processed {count} files, current fiile is {file_name} ")
            return self.connector.store.add(nodes)

    def delete(self, **kwargs) -> bool:
        return self.connector.delete(**kwargs)
