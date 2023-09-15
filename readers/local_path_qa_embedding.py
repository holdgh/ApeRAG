#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
from typing import List

from llama_index.data_structs.data_structs import Node
from llama_index.schema import NodeRelationship, RelatedNodeInfo
from llama_index.vector_stores.types import NodeWithEmbedding

from config import settings
from readers.local_path_embedding import LocalPathEmbedding
from readers.qa_generator import AlgoletQAGenerator, BaiChuanQAGenerator

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class LocalPathQAEmbedding(LocalPathEmbedding):

    def __init__(self, predictor, **kwargs):
        super().__init__(**kwargs)
        self.qa_generator = BaiChuanQAGenerator(predictor=predictor)
        self.qa_pairs = []

    def load_data(self) -> list[str]:
        docs, file_name = self.reader.load_data()
        if not docs:
            return []

        if not settings.ENABLE_QA_GENERATOR:
            return []

        nodes: List[NodeWithEmbedding] = []
        for doc in docs:

            doc.text = doc.text.strip()

            # ignore page less than 30 characters
            text_size_threshold = 30
            if len(doc.text) < text_size_threshold:
                logger.warning("ignore page less than %d characters: %s",
                               text_size_threshold, doc.metadata.get("name", None))
                continue

            # ignore page with content ratio less than 0.75
            content_ratio = doc.metadata.get("content_ratio", 1)
            content_ratio_threshold = 0.75
            if content_ratio < content_ratio_threshold:
                logger.warning("ignore page with content ratio less than %f: %s",
                               content_ratio_threshold, doc.metadata.get("name", None))
                continue

            # ignore page larger than 200 characters
            large_doc_threshold = 200
            if len(doc.text) > large_doc_threshold:
                logger.warning("ignore doc larger than %d", large_doc_threshold)
                continue

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
            qa_pairs = self.qa_generator.gen_qa_pairs(text)
            if len(qa_pairs) == 0:
                continue

            self.qa_pairs.extend(qa_pairs)

            for q, a in qa_pairs:
                node = Node(
                    text=f"{a}",
                    doc_id=doc.doc_id,
                )
                logger.warning("pair question [%s] with answer [%s] in document %s" % (q, a, doc.metadata["name"]))
                node.relationships = {
                    NodeRelationship.SOURCE: RelatedNodeInfo(
                        node_id=node.node_id, metadata={"source": f"{doc.metadata['name']}"}
                    )
                }
                vector = self.embedding.embed_query(q)
                nodes.append(NodeWithEmbedding(node=node, embedding=vector))
        print(f"processed file: {file_name} ")
        return self.connector.store.add(nodes)

    def delete(self, **kwargs) -> bool:
        return self.connector.delete(**kwargs)
