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

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class Source(str, Enum):
    EMAIL = "email"
    FILE = "file"
    CHAT = "chat"
    WEB = "web"
    APP = "app"


class Document(BaseModel):
    source: Source = Source.FILE
    doc_id: str = None
    text: str = None


class DocumentMetadata(BaseModel):
    source: Optional[Source] = None
    source_id: Optional[str] = None
    url: Optional[str] = None
    created_at: Optional[str] = None
    author: Optional[str] = None


class DocumentChunkMetadata(DocumentMetadata):
    doc_id: Optional[str] = None


class DocumentChunk(BaseModel):
    id: Optional[str] = None
    text: str
    metadata: DocumentChunkMetadata
    embedding: Optional[List[float]] = None


class DocumentWithScore(BaseModel):
    source: Source = Source.FILE
    doc_id: str = None
    text: str = None
    score: float
    metadata: dict = None
    rank_before: int = -1

    def get_source_file(self) -> str:
        return self.metadata["source"]


class DocumentMetadataFilter(BaseModel):
    doc_id: Optional[str] = None
    source: Optional[Source] = None
    source_id: Optional[str] = None
    author: Optional[str] = None
    start_date: Optional[str] = None  # any date string format
    end_date: Optional[str] = None  # any date string format


class Query(BaseModel):
    query: str
    top_k: Optional[int] = 3


class QueryWithEmbedding(Query):
    embedding: List[float]


class QueryResult(BaseModel):
    query: str
    results: List[DocumentWithScore]


def get_packed_answer(results, limit_length: Optional[int] = 0) -> str:
    text_chunks = []
    for r in results:
        prefix = ""
        if r.metadata.get("url"):
            prefix = "The following information is from: " + r.metadata.get("url") + "\n"
        text_chunks.append(prefix + r.text)
    answer_text = "\n\n".join(text_chunks)
    if limit_length != 0:
        return answer_text[:limit_length]
    else:
        return answer_text


class UpsertRequest(BaseModel):
    documents: List[Document]


class UpsertResponse(BaseModel):
    ids: List[str]


class QueryRequest(BaseModel):
    queries: List[Query]


class QueryResponse(BaseModel):
    results: List[QueryResult]


class DeleteRequest(BaseModel):
    ids: Optional[List[str]] = None
    filter: Optional[DocumentMetadataFilter] = None
    delete_all: Optional[bool] = False


class DeleteResponse(BaseModel):
    success: bool
