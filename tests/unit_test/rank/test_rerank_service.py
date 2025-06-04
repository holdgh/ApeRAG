import pytest

from aperag.query.query import DocumentWithScore
from aperag.rank.rerank_service import RerankService

# ---------- Basic Test Data ----------
QUERY = "hello world"

DOC_MATCH = "hello world"  # Highly relevant to query
DOC_PARTIAL = "hello there, beautiful world!"  # Moderately relevant
DOC_UNRELATED = "lorem ipsum dolor sit amet"  # Mostly irrelevant

BASE_RESULTS = [
    DocumentWithScore(text=DOC_UNRELATED, score=0.1),
    DocumentWithScore(text=DOC_MATCH, score=0.1),
    DocumentWithScore(text=DOC_PARTIAL, score=0.1),
]


# ---------- Test Cases ----------


@pytest.mark.asyncio
async def test_rerank_service_initialization():
    """
    Test that RerankService can be created with required parameters
    """
    service = RerankService(
        rerank_provider="jina_ai",
        rerank_model="test-model",
        rerank_service_url="https://example.com",
        rerank_service_api_key="test-key",
    )

    assert service.rerank_provider == "jina_ai"
    assert service.model == "test-model"
    assert service.api_base == "https://example.com"
    assert service.api_key == "test-key"


@pytest.mark.asyncio
async def test_rerank_empty_results():
    """
    Test that reranking empty results returns empty list
    """
    service = RerankService(
        rerank_provider="jina_ai",
        rerank_model="test-model",
        rerank_service_url="https://example.com",
        rerank_service_api_key="test-key",
    )

    result = await service.rank("query", [])
    assert result == []


# Integration tests that require real API credentials
# These tests should be run with proper configuration
@pytest.mark.integration
@pytest.mark.asyncio
async def test_rerank_with_real_service(rerank_service_config):
    """
    Integration test with real rerank service.
    Requires rerank_service_config fixture with real credentials.
    """
    if not rerank_service_config:
        pytest.skip("No rerank service configuration provided")

    service = RerankService(**rerank_service_config)
    ranked = await service.rank(QUERY, BASE_RESULTS)

    # Basic assertions
    assert len(ranked) == len(BASE_RESULTS)
    assert all(isinstance(d, DocumentWithScore) for d in ranked)
    assert {d.text for d in ranked} == {d.text for d in BASE_RESULTS}
