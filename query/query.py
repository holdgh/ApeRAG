from pydantic import BaseModel
from typing import List, Optional
from enum import Enum


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


class DocumentWithScore(BaseModel):
    source: Source = Source.FILE
    doc_id: str = None
    text: str = None
    score: float


class DocumentMetadata(BaseModel):
    source: Optional[Source] = None
    source_id: Optional[str] = None
    url: Optional[str] = None
    created_at: Optional[str] = None
    author: Optional[str] = None


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
