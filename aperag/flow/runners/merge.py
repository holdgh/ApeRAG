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

from typing import List, Optional, Tuple

from pydantic import BaseModel, Field

from aperag.flow.base.exceptions import ValidationError
from aperag.flow.base.models import BaseNodeRunner, SystemInput, register_node_runner
from aperag.query.query import DocumentWithScore


class MergeInput(BaseModel):
    merge_strategy: str = Field("union", description="How to merge results")
    deduplicate: bool = Field(True, description="Whether to deduplicate merged results")
    vector_search_docs: Optional[List[DocumentWithScore]] = Field(
        default_factory=list, description="Vector search docs"
    )
    fulltext_search_docs: Optional[List[DocumentWithScore]] = Field(
        default_factory=list, description="Fulltext search docs"
    )
    graph_search_docs: Optional[List[DocumentWithScore]] = Field(default_factory=list, description="Graph search docs")
    summary_search_docs: Optional[List[DocumentWithScore]] = Field(
        default_factory=list, description="Summary search docs"
    )
    vision_search_docs: Optional[List[DocumentWithScore]] = Field(
        default_factory=list, description="Vision search docs"
    )


class MergeOutput(BaseModel):
    docs: List[DocumentWithScore]


@register_node_runner(
    "merge",
    input_model=MergeInput,  # 合并节点入参定义
    output_model=MergeOutput,  # 合并节点出参定义
)
class MergeNodeRunner(BaseNodeRunner):  # 知识库检索的合并节点【汇总合并多种索引检索的结果】
    async def run(self, ui: MergeInput, si: SystemInput) -> Tuple[MergeOutput, dict]:  # 直接拼接【可基于分段内容去重】各种索引库的检索结果
        """
        Run merge node. ui: user input; si: system input (SystemInput).
        Returns (output, system_output)
        """
        docs_a: List[DocumentWithScore] = ui.vector_search_docs or []
        docs_b: List[DocumentWithScore] = ui.fulltext_search_docs or []
        docs_c: List[DocumentWithScore] = ui.graph_search_docs or []
        docs_d: List[DocumentWithScore] = ui.summary_search_docs or []
        docs_e: List[DocumentWithScore] = ui.vision_search_docs or []
        merge_strategy: str = ui.merge_strategy
        deduplicate: bool = ui.deduplicate

        if merge_strategy not in ["union"]:
            raise ValidationError(f"Unknown merge strategy: {merge_strategy}")

        all_docs = docs_a + docs_b + docs_c + docs_d + docs_e  # 直接拼接各种索引库的检索结果
        if deduplicate:  # 基于分段内容去重
            seen = set()
            unique_docs = []
            for doc in all_docs:
                if doc.text not in seen:
                    seen.add(doc.text)
                    unique_docs.append(doc)
            return MergeOutput(docs=unique_docs), {}
        return MergeOutput(docs=all_docs), {}
