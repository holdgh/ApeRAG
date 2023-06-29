from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from llama_index.vector_stores.qdrant import QdrantVectorStore
import qdrant_client
from qdrant_client.models import Distance,VectorParams
from qdrant_client.http.models import (
    ScoredPoint,
    SearchRequest,
    Filter,
    FieldCondition,
    Field,
    MatchValue,
    Range
)
from vectorstore.base import VectorStoreConnector
from query.query import QueryWithEmbedding, DocumentWithScore, DocumentMetadataFilter
from utils.date import to_unix_timestamp


class QdrantVectorStoreConnector(VectorStoreConnector):
    def __init__(self, ctx: Dict[str, Any], **kwargs: Any) -> None:
        super().__init__(ctx, **kwargs)
        self.ctx = ctx
        self.collection_name = ctx.get("collection", "collection")

        self.url = ctx.get("url", "http://localhost")
        self.port = ctx.get("port", 6333)
        self.grpc_port = ctx.get("grpc_port", 6334)
        self.prefer_grpc = ctx.get("prefer_grpc", False)
        self.https = ctx.get("https", False)
        self.timeout = ctx.get("timeout", 300)
        self.vector_size = ctx.get("vector_size", 1536)
        self.distance = ctx.get("distance", "Cosine")

        if self.url == ":memory:":
            self.client = qdrant_client.QdrantClient(":memory:")
        else:
            self.client = qdrant_client.QdrantClient(
                url=self.url,
                port=self.port,
                grpc_port=self.grpc_port,
                prefer_grpc=self.prefer_grpc,
                https=self.https,
                timeout=self.timeout,
                **kwargs,
            )

        self.store = QdrantVectorStore(
            client=self.client,
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=self.vector_size, distance=self.distance))

    def search(self,
               query: QueryWithEmbedding,
               **kwargs):

        limit = kwargs.get("limit", 3)
        consistency = kwargs.get("consistency", "majority")
        search_params = kwargs.get("search_params")

        hits = self.client.search(
            collection_name=self.collection_name,
            query_vector=query.embedding,
            with_vectors=True,
            limit=query.top_k,
            consistency=consistency,
            search_params=search_params,
        )

    def _convert_query_to_search_request(
                self, query: QueryWithEmbedding
        ) -> SearchRequest:
            return SearchRequest(
                vector=query.embedding,
                filter=self._convert_metadata_filter_to_qdrant_filter(query.filter),
                limit=query.top_k,  # type: ignore
                with_payload=True,
                with_vector=False,
            )

    def _convert_scored_point_to_document_with_score(
                self, scored_point: ScoredPoint
    ) -> DocumentWithScore:
        payload = scored_point.payload or {}
        return DocumentWithScore(
            id=payload.get("id"),
            text=scored_point.payload.get("text"),  # type: ignore
            metadata=scored_point.payload.get("metadata"),  # type: ignore
            embedding=scored_point.vector,  # type: ignore
            score=scored_point.score,
        )

    def _convert_metadata_filter_to_qdrant_filter(
            self,
            metadata_filter: Optional[DocumentMetadataFilter] = None,
            ids: Optional[List[str]] = None,
    ) -> Optional[Filter]:
        if metadata_filter is None and ids is None:
            return None

        must_conditions, should_conditions = [], []

        # Filtering by document ids
        if ids and len(ids) > 0:
            for document_id in ids:
                should_conditions.append(
                    FieldCondition(
                        key="metadata.document_id",
                        match=MatchValue(value=document_id),
                    )
                )

        # Equality filters for the payload attributes
        if metadata_filter:
            meta_attributes_keys = {
                "document_id": "metadata.document_id",
                "source": "metadata.source",
                "source_id": "metadata.source_id",
                "author": "metadata.author",
            }

            for meta_attr_name, payload_key in meta_attributes_keys.items():
                attr_value = getattr(metadata_filter, meta_attr_name)
                if attr_value is None:
                    continue

                must_conditions.append(
                    FieldCondition(
                        key=payload_key, match=MatchValue(value=attr_value)
                    )
                )

            # Date filters use range filtering
            start_date = metadata_filter.start_date
            end_date = metadata_filter.end_date
            if start_date or end_date:
                gte_filter = (
                    to_unix_timestamp(start_date) if start_date is not None else None
                )
                lte_filter = (
                    to_unix_timestamp(end_date) if end_date is not None else None
                )
                must_conditions.append(
                    FieldCondition(
                        key="created_at",
                        range=Range(
                            gte=gte_filter,
                            lte=lte_filter,
                        ),
                    )
                )

        if 0 == len(must_conditions) and 0 == len(should_conditions):
            return None

        return Filter(must=must_conditions, should=should_conditions)
