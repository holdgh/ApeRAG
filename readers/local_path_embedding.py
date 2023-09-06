#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import faulthandler
import re
from typing import Any, List, Optional, Dict

from llama_index import (
    LangchainEmbedding,
)
from llama_index.data_structs.data_structs import Node
from llama_index.schema import NodeRelationship, RelatedNodeInfo
from llama_index.vector_stores.types import NodeWithEmbedding

from readers.base_embedding import DocumentBaseEmbedding
from readers.local_path_reader import InteractiveSimpleDirectoryReader
from vectorstore.connector import VectorStoreConnectorAdaptor

logger = logging.getLogger(__name__)

faulthandler.enable()



class LocalPathEmbedding(DocumentBaseEmbedding):
    def __init__(
            self,
            vector_store_adaptor: VectorStoreConnectorAdaptor,
            embedding_model: LangchainEmbedding = None,
            vector_size: int = 0,
            input_file_metadata_list: Optional[List[Dict[str, Any]]] = None,
            **kwargs: Any,
    ) -> None:
        super().__init__(vector_store_adaptor, embedding_model, vector_size)
        input_files = kwargs.get("input_files", [])
        if input_files and input_file_metadata_list:
            metadata_mapping = {}
            for idx, metadata in enumerate(input_file_metadata_list):
                metadata_mapping[input_files[idx]] = metadata

            def metadata_mapping_func(path: str) -> Dict[str, Any]:
                return metadata_mapping.get(path, {})
            kwargs["file_metadata"] = metadata_mapping_func
        self.reader = InteractiveSimpleDirectoryReader(**kwargs)

    def load_data(self) -> list[str]:
        docs, file_name = self.reader.load_data()
        if not docs:
            return []

        nodes: List[NodeWithEmbedding] = []
        for doc in docs:

            doc.text = doc.text.strip()

            # ignore page less than 30 characters
            # text_size_threshold = 30
            # if len(doc.text) < text_size_threshold:
            #     logger.warning("ignore page less than %d characters: %s",
            #                    text_size_threshold, doc.metadata.get("name", None))
            #     continue

            # ignore page with content ratio less than 0.8
            # content_ratio = doc.metadata.get("content_ratio", 1)
            # content_ratio_threshold = 0.8
            # if content_ratio < content_ratio_threshold:
            #     logger.warning("ignore page with content ratio less than %f: %s",
            #                    content_ratio_threshold, doc.metadata.get("name", None))
            #     continue

            paddings = []
            # padding titles of the hierarchy
            if "titles" in doc.metadata:
                paddings.append(" ".join(doc.metadata["titles"]))

            # padding user custom labels
            if "labels" in doc.metadata:
                labels = []
                for item in doc.metadata.get("labels", [{}]):
                    if not item.get("key", None) or not item.get("value", None):
                        continue
                    labels.append("%s=%s" % (item["key"], item["value"]))
                paddings.append(" ".join(labels))
            prefix = "\n\n".join(paddings)

            # embedding without the code block
            # text = re.sub(r"```.*?```", "", doc.text, flags=re.DOTALL)
            text = f"{prefix}\n{doc.text}"
            vector = self.embedding.embed_documents([text])[0]
            doc.embedding = vector
            node = Node(
                text=doc.text,
                doc_id=doc.doc_id,
            )
            node.metadata.update(doc.metadata)
            node.relationships = {
                NodeRelationship.SOURCE: RelatedNodeInfo(
                    node_id=node.node_id, metadata={"source": f"{doc.metadata['name']}"}
                )
            }
            nodes.append(NodeWithEmbedding(node=node, embedding=vector))
        print(f"processed file: {file_name} ")
        return self.connector.store.add(nodes)

    def delete(self, **kwargs) -> bool:
        return self.connector.delete(**kwargs)
