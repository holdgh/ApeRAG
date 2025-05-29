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

from llama_index.core.data_structs import Node
from llama_index.core.schema import NodeRelationship, RelatedNodeInfo
from llama_index.core.vector_stores.types import NodeWithEmbedding
from llama_index.embeddings.langchain import LangchainEmbedding

from aperag.embed.base_embedding import DocumentBaseEmbedding
from aperag.vectorstore.connector import VectorStoreConnectorAdaptor


class QAEmbedding(DocumentBaseEmbedding):
    def __init__(
        self,
        question: str,
        answer: str,
        vector_store_adaptor: VectorStoreConnectorAdaptor,
        embedding_model: LangchainEmbedding = None,
        vector_size: int = 0,
    ):
        super().__init__(vector_store_adaptor, embedding_model, vector_size)
        self.question = question
        self.answer = answer

    def load_data(self):
        vector = self.embedding.embed_query(self.question)
        node = Node(
            text=self.answer,
        )
        node.relationships = {
            NodeRelationship.SOURCE: RelatedNodeInfo(node_id=node.node_id, metadata={"source": f"{self.question}"})
        }
        return self.connector.store.add([NodeWithEmbedding(node=node, embedding=vector)])
