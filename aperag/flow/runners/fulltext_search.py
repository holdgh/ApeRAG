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

import logging
from typing import List, Optional, Tuple

from pydantic import BaseModel, Field

from aperag.aperag_config import settings
from aperag.db.models import Collection
from aperag.db.ops import async_db_ops
from aperag.flow.base.models import BaseNodeRunner, SystemInput, register_node_runner
from aperag.index.fulltext_index import extract_keywords
from aperag.query.query import DocumentWithScore
from aperag.utils.utils import generate_vector_db_collection_name

logger = logging.getLogger(__name__)


class FulltextSearchInput(BaseModel):
    query: str = Field(..., description="User's question or query")
    top_k: int = Field(5, description="Number of top results to return")
    collection_ids: Optional[List[str]] = Field(default_factory=list, description="Collection IDs")
    keywords: Optional[List[str]] = Field(
        default_factory=list, description="Custom keywords to use for fulltext search"
    )
    chat_id: Optional[str] = Field(None, description="Chat ID to filter chat documents")


class FulltextSearchOutput(BaseModel):
    docs: List[DocumentWithScore]


# Database operations interface
class FulltextSearchRepository:
    """Repository interface for fulltext search database operations"""

    async def get_collection(self, user, collection_id: str) -> Optional[Collection]:
        """Get collection by ID for the user"""
        return await async_db_ops.query_collection(user, collection_id)


# Business logic service
class FulltextSearchService:
    """Service class containing fulltext search business logic"""

    def __init__(self, repository: FulltextSearchRepository):
        self.repository = repository

    async def execute_fulltext_search(
        self,
        user,
        query: str,
        top_k: int,
        collection_ids: List[str],
        keywords: List[str],
        chat_id: Optional[str] = None,
    ) -> List[DocumentWithScore]:
        """Execute fulltext search with given parameters"""
        collection = None
        if collection_ids:
            collection = await self.repository.get_collection(user, collection_ids[0])

        if not collection:
            return []

        from aperag.index.fulltext_index import fulltext_indexer

        index = generate_vector_db_collection_name(collection.id)
        if not keywords:
            # Create context for keyword extractor
            extractor_ctx = {
                "index_name": index,
                "es_host": settings.es_host,
                "es_timeout": settings.es_timeout,
                "es_max_retries": settings.es_max_retries,
                "user_id": str(user) if user else None,
            }

            # Use extract_keywords function with fallback strategy
            keywords = await extract_keywords(query, extractor_ctx)

        keywords = list(set(keywords))

        # Find the related documents using keywords
        docs = await fulltext_indexer.search_document(index, keywords, top_k * 3, chat_id=chat_id)

        # Add recall type metadata
        for doc in docs:
            doc.metadata["recall_type"] = "fulltext_search"

        return docs


@register_node_runner(
    "fulltext_search",
    input_model=FulltextSearchInput,
    output_model=FulltextSearchOutput,
)
class FulltextSearchNodeRunner(BaseNodeRunner):
    def __init__(self):
        self.repository = FulltextSearchRepository()
        self.service = FulltextSearchService(self.repository)

    async def run(self, ui: FulltextSearchInput, si: SystemInput) -> Tuple[FulltextSearchOutput, dict]:
        """
        Run fulltext search node. ui: user input; si: system input (SystemInput).
        Returns (output, system_output)
        """
        chat_id = ui.chat_id or getattr(si, "chat_id", None)

        collection_ids = ui.collection_ids or getattr(si, "collection_ids", [])

        docs = await self.service.execute_fulltext_search(
            user=si.user,
            query=si.query,
            top_k=ui.top_k,
            collection_ids=collection_ids,
            keywords=ui.keywords,
            chat_id=chat_id,
        )
        return FulltextSearchOutput(docs=docs), {}
