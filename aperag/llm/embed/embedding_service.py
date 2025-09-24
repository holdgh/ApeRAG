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

from __future__ import annotations

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Sequence, Tuple

import litellm

from aperag.llm.llm_error_types import (
    BatchProcessingError,
    EmbeddingError,
    EmptyTextError,
    wrap_litellm_error,
)

logger = logging.getLogger(__name__)


class EmbeddingService:  # embedding模型服务定义
    def __init__(
        self,
        embedding_provider: str,
        embedding_model: str,
        embedding_service_url: str,
        embedding_service_api_key: str,
        embedding_max_chunks_in_batch: int,
        multimodal: bool = False,
        caching: bool = True,
    ):
        self.embedding_provider = embedding_provider
        self.model = embedding_model
        self.api_base = embedding_service_url
        self.api_key = embedding_service_api_key
        self.max_chunks = embedding_max_chunks_in_batch
        self.max_workers = 8
        self.multimodal = multimodal
        self.caching = caching

    def embed_documents(self, contents: List[str]) -> List[List[float]]:  # 对分段内容列表批量embedding处理，返回结果为embedding向量列表，一个分段对应一个embedding向量
        """
        Embed multiple documents in parallel batches.

        Args:
            contents: List of documents (texts or base64-encoded images) to embed

        Returns:
            List of embedding vectors in the same order as input contents
        """
        # -- 分段文本列表非空校验
        # Validate inputs
        if not contents:
            raise EmptyTextError(0)

        # Check for empty contents
        empty_indices = [i for i, text in enumerate(contents) if not text or not text.strip()]
        if empty_indices:
            logger.warning(f"Found {len(empty_indices)} empty content at indices: {empty_indices}")
            if len(empty_indices) == len(contents):
                raise EmptyTextError(len(empty_indices))

        try:
            # -- 分段文本清洗【将换行符替换为空格】
            # Clean contents by replacing newlines with spaces
            clean_contents = [t.replace("\n", " ") if t and t.strip() else " " for t in contents]
            # -- 批量embedding处理【多线程方式】
            # Determine batch size (use max_chunks or process all at once if not set)
            batch_size = self.max_chunks or len(clean_contents)

            # Store results with original indices to ensure correct ordering
            results_dict: Dict[int, List[float]] = {}

            with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
                futures = []

                # Submit batches for processing with their starting indices
                for start in range(0, len(clean_contents), batch_size):
                    batch = clean_contents[start : start + batch_size]
                    # Pass both the batch and starting index to track position
                    future = pool.submit(self._embed_batch_with_indices, batch, start)  # 真正的对文本列表进行embedding处理，结果中包含相应文本在原始文本列表中的序号
                    futures.append(future)

                # Process completed futures and store results by index
                failed_batches = []
                for future in as_completed(futures):
                    try:
                        # Get results with their original indices
                        batch_results = future.result()
                        for idx, embedding in batch_results:
                            results_dict[idx] = embedding  # 构造embedding结果字典：{序号：embedding向量}
                    except Exception as e:
                        failed_batches.append(str(e))
                        logger.error(f"Batch processing failed: {e}")

                if failed_batches:
                    raise BatchProcessingError(
                        batch_size=batch_size,
                        reason=f"Failed to process {len(failed_batches)} batches: {failed_batches[:3]} "
                        f"contents: {contents}",
                    )

            # Reconstruct the result list in the original order
            results = [results_dict[i] for i in range(len(clean_contents))]  # 列表化重构。保留原始顺序，也即分段文本与embedding向量的对应顺序
            return results
        except (EmptyTextError, BatchProcessingError, EmbeddingError):
            # Re-raise our custom embedding errors
            raise
        except Exception as e:
            logger.error(f"Document embedding failed: {str(e)}")
            raise wrap_litellm_error(e, "embedding", self.embedding_provider, self.model) from e

    async def aembed_documents(self, contents: List[str]) -> List[List[float]]:
        return await asyncio.to_thread(self.embed_documents, contents)

    def embed_query(self, content: str) -> List[float]:
        """
        Embed a single query content.

        Args:
            content: content to embed

        Returns:
            List of floats representing the embedding vector
        """
        if not content or not content.strip():
            raise EmptyTextError(1)

        try:
            return self.embed_documents([content])[0]
        except (EmptyTextError, EmbeddingError):
            # Re-raise our custom embedding errors
            raise
        except Exception as e:
            logger.error(f"Query embedding failed: {str(e)}")
            raise wrap_litellm_error(e, "embedding", self.embedding_provider, self.model) from e

    async def aembed_query(self, content: str) -> List[float]:
        return await asyncio.to_thread(self.embed_query, content)

    def is_multimodal(self) -> bool:
        return self.multimodal

    def _embed_batch_with_indices(self, batch: Sequence[str], start_idx: int) -> List[Tuple[int, List[float]]]:  # 对文本列表进行embedding处理
        """Process a batch of texts and return embeddings with their original indices."""
        try:
            embeddings = self._embed_batch(batch)
            # Return each embedding with its corresponding index in the original list
            return [(start_idx + i, embedding) for i, embedding in enumerate(embeddings)]  # 结果中含有相应文本在原始文本列表中的序号“start_idx + i”
        except Exception as e:
            logger.error(f"Batch embedding with indices failed: {str(e)}")
            # Convert litellm errors for batch processing
            raise wrap_litellm_error(e, "embedding", self.embedding_provider, self.model) from e

    def _embed_batch(self, batch: Sequence[str]) -> List[List[float]]:  # 基于litellm工具包调用远程embedding模型服务，对文本列表进行批量embedding处理
        """
        Embed a batch of contents using litellm.

        Args:
            batch: Sequence of contents to embed

        Returns:
            List of embedding vectors

        Raises:
            EmbeddingError: If embedding fails
        """
        """
        litellm 是一个轻量级的 Python 库，主要作用是统一不同大语言模型（LLM）的 API 调用接口，
        让开发者可以用相同的代码逻辑调用不同厂商的模型（如 OpenAI、Anthropic、Google、国内的智谱、讯飞等）。
        
        litellm 本身不运行模型，而是作为 “中间层” 转发请求：
            当你调用 litellm.completion() 时，它会根据 model 参数识别目标厂商，将统一格式的请求转换为该厂商的 API 格式，
            再通过 HTTP 等协议远程调用其 API 接口，最后将返回结果转换为统一格式返回给你。
        """
        try:
            response = litellm.embedding(
                custom_llm_provider=self.embedding_provider,
                model=self.model,
                api_base=self.api_base,
                api_key=self.api_key,
                input=list(batch),
                caching=self.caching,
            )

            if not response or "data" not in response:
                raise EmbeddingError(
                    "Invalid response format from embedding API",
                    {"provider": self.embedding_provider, "model": self.model, "batch_size": len(batch)},
                )

            embeddings = [item["embedding"] for item in response["data"]]

            # Validate embedding dimensions
            if embeddings and len(set(len(emb) for emb in embeddings)) > 1:
                dimensions = [len(emb) for emb in embeddings]
                logger.warning(f"Inconsistent embedding dimensions: {set(dimensions)}")

            return embeddings
        except Exception as e:
            logger.error(f"Batch embedding API call failed: {str(e)}")
            # Convert litellm errors to our custom types
            raise wrap_litellm_error(e, "embedding", self.embedding_provider, self.model) from e
