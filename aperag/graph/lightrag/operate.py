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

"""
LightRAG Module for ApeRAG

This module is based on the original LightRAG project with extensive modifications.

Original Project:
- Repository: https://github.com/HKUDS/LightRAG
- Paper: "LightRAG: Simple and Fast Retrieval-Augmented Generation" (arXiv:2410.05779)
- Authors: Zirui Guo, Lianghao Xia, Yanhua Yu, Tu Ao, Chao Huang
- License: MIT License

Modifications by ApeRAG Team:
- Removed global state management for true concurrent processing
- Added stateless interfaces for Celery/Prefect integration
- Implemented instance-level locking mechanism
- Enhanced error handling and stability
- See changelog.md for detailed modifications
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import time
from collections import Counter, defaultdict
from typing import Any, AsyncIterator

from aperag.concurrent_control import get_or_create_lock

from .base import (
    BaseGraphStorage,
    BaseKVStorage,
    BaseVectorStorage,
    QueryParam,
    TextChunkSchema,
)
from .prompt import GRAPH_FIELD_SEP, PROMPTS
from .types import GraphNodeData, GraphNodeDataDict, MergeSuggestion
from .utils import (
    LightRAGLogger,
    Tokenizer,
    clean_str,
    compute_mdhash_id,
    get_conversation_turns,
    is_float_regex,
    logger,
    normalize_extracted_info,
    pack_user_ass_to_openai_messages,
    process_combine_contexts,
    split_string_by_multi_markers,
    timing_wrapper,
    truncate_list_by_token_size,
)


def chunking_by_token_size(
    tokenizer: Tokenizer,
    content: str,
    split_by_character: str | None = None,
    split_by_character_only: bool = False,
    overlap_token_size: int = 128,
    max_token_size: int = 1024,
) -> list[dict[str, Any]]:  # 按照长度【和分隔符】分段操作
    tokens = tokenizer.encode(content)  # 分词器编码
    results: list[dict[str, Any]] = []
    if split_by_character:  # None
        raw_chunks = content.split(split_by_character)
        new_chunks = []
        if split_by_character_only:
            for chunk in raw_chunks:
                _tokens = tokenizer.encode(chunk)
                new_chunks.append((len(_tokens), chunk))
        else:
            for chunk in raw_chunks:
                _tokens = tokenizer.encode(chunk)
                if len(_tokens) > max_token_size:
                    for start in range(0, len(_tokens), max_token_size - overlap_token_size):
                        chunk_content = tokenizer.decode(_tokens[start : start + max_token_size])
                        new_chunks.append((min(max_token_size, len(_tokens) - start), chunk_content))
                else:
                    new_chunks.append((len(_tokens), chunk))
        for index, (_len, chunk) in enumerate(new_chunks):
            results.append(
                {
                    "tokens": _len,
                    "content": chunk.strip(),
                    "chunk_order_index": index,
                }
            )
    else:  # 分隔符为None时
        for index, start in enumerate(range(0, len(tokens), max_token_size - overlap_token_size)):
            chunk_content = tokenizer.decode(tokens[start : start + max_token_size])  # 按照长度分段
            results.append(
                {
                    "tokens": min(max_token_size, len(tokens) - start),  # 分段长度
                    "content": chunk_content.strip(),  # 分段内容
                    "chunk_order_index": index,  # 分段的索引【相对整个文档的content而言】
                }
            )
    return results


@timing_wrapper("_handle_entity_relation_summary")
async def _handle_entity_relation_summary(
    entity_or_relation_name: str,  # 实体或关系名称
    description: str,  # 实体或关系描述【分隔符拼接的10个以上的实体或关系描述字符串】
    llm_model_func: callable,
    tokenizer: Tokenizer,
    llm_model_max_token_size: int,
    summary_to_max_tokens: int,
    language: str,
    lightrag_logger: LightRAGLogger,
) -> str:  # 基于llm对同一实体/关系名称的多个实体/关系描述做摘要总结
    """Handle entity relation summary
    For each entity or relation, input is the combined description of already existing description and new description.
    If too long, use LLM to summarize.
    """
    """
    1. 类型注解（: callable）
        - : callable 是 Python 的类型注解（type hint），用于指定变量 use_llm_func 的类型为 “可调用对象”。
        - 可调用对象（callable） 指任何可以像函数一样被调用的对象，包括函数、类、带 __call__ 方法的实例等。例如：普通函数、lambda 表达式、类的构造方法等。
        - 这里的类型注解主要起提示作用，告诉开发者（或 IDE）：use_llm_func 应该是一个可以被调用的对象（如函数），后续可能会以 use_llm_func(...) 的形式使用。

    2. 变量赋值（= llm_model_func）
        - 等号 = 表示将变量 use_llm_func 指向 llm_model_func 这个对象。
        - 结合类型注解 callable 可知，llm_model_func 应该是一个函数（或其他可调用对象），通常用于与大语言模型（LLM）交互（例如调用模型生成文本、处理提示词等）。
    
    3. 典型场景与作用
    这种写法常见于需要 “灵活替换函数” 的场景，例如：
        - llm_model_func 可能是一个默认的 LLM 调用函数（如调用 GPT-3.5），而 use_llm_func 作为 “实际使用的函数”，后续可以根据需求替换为其他函数（如调用 Claude、Llama 等模型）。
        - 通过统一变量名 use_llm_func 来调用函数，避免直接硬编码 llm_model_func，提高代码的可维护性和灵活性。
    """
    """
    定义一个名为 use_llm_func 的变量，指定它是可调用对象，并将其初始化为 llm_model_func。
    目的是通过统一的变量名来使用 LLM 相关功能，同时通过类型注解明确其用途，提升代码的可读性和可扩展性。
    """
    use_llm_func: callable = llm_model_func  # llm操作，可调用对象

    tokens = tokenizer.encode(description)  # 对实体或关系描述进行分词编码

    prompt_template = PROMPTS["summarize_entity_descriptions"]
    use_description = tokenizer.decode(tokens[:llm_model_max_token_size])  # 基于lightrag配置的llm输入token最大限制对实体描述进行截取
    context_base = dict(
        entity_name=entity_or_relation_name,  # 实体或关系名称
        description_list=use_description.split(GRAPH_FIELD_SEP),  # 基于分隔符将描述内容还原为字符串列表
        language=language,  # 语言参数 "The same language like input text"
    )  # 构造实体或关系描述上下文信息
    use_prompt = prompt_template.format(**context_base)  # 基于提示词模板和上下文信息完善最终提示词

    lightrag_logger.debug(f"Trigger summary: {entity_or_relation_name}")

    summary = await use_llm_func(use_prompt, max_tokens=summary_to_max_tokens)  # 利用大模型对实体或关系描述进行摘要总结
    return summary


async def _handle_single_entity_extraction(
    record_attributes: list[str],  # 大模型输出的实体记录，组成模式：[实体标识【entity】，实体名称， 实体类型，实体描述]
    chunk_key: str,  # 分段id
    file_path: str = "unknown_source",  # 原始文档路径
):
    # -- 非实体信息过滤
    if len(record_attributes) < 4 or '"entity"' not in record_attributes[0]:
        return None
    # -- 实体名称清理
    # Clean and validate entity name
    entity_name = clean_str(record_attributes[1]).strip()
    if not entity_name:
        logger.warning(f"Entity extraction error: empty entity name in: {record_attributes}")
        return None

    # Normalize entity name
    entity_name = normalize_extracted_info(entity_name, is_entity=True)  # 实体名称规范化处理
    # -- 实体类型清理
    # Clean and validate entity type
    entity_type = clean_str(record_attributes[2]).strip('"')
    if not entity_type.strip() or entity_type.startswith('("'):
        logger.warning(f"Entity extraction error: invalid entity type in: {record_attributes}")
        return None
    # -- 实体描述清理
    # Clean and validate description
    entity_description = clean_str(record_attributes[3])
    entity_description = normalize_extracted_info(entity_description)

    if not entity_description.strip():
        logger.warning(f"Entity extraction error: empty description for entity '{entity_name}' of type '{entity_type}'")
        return None
    # -- 构造实体信息字典
    return dict(
        entity_name=entity_name,  # 实体名称
        entity_type=entity_type,  # 实体类型
        description=entity_description,  # 实体描述
        source_id=chunk_key,  # 分段id
        file_path=file_path,  # 原始文档路径
    )


async def _handle_single_relationship_extraction(
    record_attributes: list[str],  # 大模型输出的边记录，组成模式：[关系标识【relationship】，源实体名称，目标实体名称，关系描述，关系关键词，权重]
    chunk_key: str,  # 分段id
    file_path: str = "unknown_source",  # 原始文档路径
):
    # -- 非关系信息过滤
    if len(record_attributes) < 5 or '"relationship"' not in record_attributes[0]:  # TODO 这里长度是否应该改为6
        return None
    # -- 起止实体名称清理
    # add this record as edge
    source = clean_str(record_attributes[1])
    target = clean_str(record_attributes[2])

    # Normalize source and target entity names
    source = normalize_extracted_info(source, is_entity=True)
    target = normalize_extracted_info(target, is_entity=True)
    if source == target:  # 起止实体相同时，直接返回none，也即关系无效
        logger.debug(f"Relationship source and target are the same in: {record_attributes}")
        return None
    # -- 关系描述清理
    edge_description = clean_str(record_attributes[3])
    edge_description = normalize_extracted_info(edge_description)
    # -- 关系关键词清理
    edge_keywords = normalize_extracted_info(clean_str(record_attributes[4]), is_entity=True)
    edge_keywords = edge_keywords.replace("，", ",")

    edge_source_id = chunk_key
    # -- 获取权重【默认权重为1】
    weight = (
        float(record_attributes[-1].strip('"').strip("'"))
        if is_float_regex(record_attributes[-1].strip('"').strip("'"))
        else 1.0
    )
    return dict(
        src_id=source,  # 源节点id【源实体名称】
        tgt_id=target,  # 目标节点id【目标实体名称】
        weight=weight,  # 权重
        description=edge_description,  # 边描述【关系描述】
        keywords=edge_keywords,  # 边关键词【关系关键词】
        source_id=edge_source_id,  # 来源id【分段id】
        file_path=file_path,  # 原始文档路径
    )


async def _merge_nodes_then_upsert(
    entity_name: str,
    nodes_data: list[dict],
    knowledge_graph_inst: BaseGraphStorage,
    llm_model_func: callable,
    tokenizer: Tokenizer,
    llm_model_max_token_size: int,
    summary_to_max_tokens: int,
    language: str,
    force_llm_summary_on_merge: int,
    lightrag_logger: LightRAGLogger | None = None,
    workspace: str = "",
):  # 对同一实体名称的实体信息列表做合并【摘要】，得到为唯一的实体信息，并保存或更新到数据库，返回实体结构化信息
    """
    功能：合并多个名称相同的实体节点，并将结果放入知识图谱中。

    此函数通过以下方式处理实体重复数据删除：
    1. 从知识图中检索现有实体数据
    2. 将现有数据与新的实体数据合并
    3. 通过聚合确定最终的实体属性
    4. 可选地使用LLM来总结冗长的描述
    5. 将合并后的实体放回知识图谱

    参数:
        entity_name：要合并的实体名称
        nodes_data：要合并的新实体数据字典列表
        knowledge_graph_inst：知识图存储实例
        llm_model_func：用于描述汇总的LLM函数
        tokenizer：文本处理的tokenizer
        llm_model_max_token_size: LLM输入token的最大数量
        summary_to_max_tokens：摘要输出的最大令牌数
        language：llm输出摘要的语言
        force_llm_summary_on_merge：触发LLM摘要操作的阈值
        lightrag_logger：可选的记录器实例
        workspace：用于创建锁的工作区标识符

    返回:
        dict：合并后最终保存到数据库的节点数据
    """
    """
    Merge multiple entity nodes with the same name and upsert the result to knowledge graph.

    This function handles entity deduplication by:
    1. Retrieving existing entity data from knowledge graph
    2. Merging existing data with new entity data
    3. Determining the final entity properties through aggregation
    4. Optionally using LLM to summarize lengthy descriptions
    5. Upserting the merged entity back to knowledge graph

    Args:
        entity_name: The name of the entity to merge
        nodes_data: List of new entity data dictionaries to merge
        knowledge_graph_inst: Knowledge graph storage instance
        llm_model_func: LLM function for description summarization
        tokenizer: Tokenizer for text processing
        llm_model_max_token_size: Maximum token size for LLM input
        summary_to_max_tokens: Maximum tokens for summary output
        language: Language for LLM summarization
        force_llm_summary_on_merge: Threshold for triggering LLM summarization
        lightrag_logger: Optional logger instance
        workspace: Workspace identifier for lock creation

    Returns:
        dict: The merged node data that was upserted
    """
    # -- 初始化各种已存在数据的变量
    # 1. Initialize containers for collecting existing entity data
    already_entity_types = []  # 已存在的实体类型
    already_source_ids = []  # 已存在的分段id
    already_description = []  # 已存在的实体描述
    already_file_paths = []  # 已存在的原始文档路径【这里对于多个文档的相同实体名称，会对其实体数据做摘要处理】 TODO 关键逻辑【解决知识库图谱的范围问题，并不是针对单个文档构建知识图谱】
    # -- 基于当前实体名称检索属于当前实体的所有已存在实体数据 TODO 关键逻辑【跨文档、跨分段】
    # 2. Retrieve existing entity from knowledge graph if it exists
    already_node = await knowledge_graph_inst.get_node(entity_name)  # 仅基于实体名称检索已存在的实体信息【由于知识图谱存储实例是知识库维度的，则表明aperag构建的知识图谱也是知识库维度的，也即一个知识库对应一个知识图谱】
    if already_node:
        # 2.1. Collect existing entity type
        already_entity_types.append(already_node["entity_type"])  # 由此可见，实体类型是唯一的

        # 2.2. Split and collect existing source IDs (multiple IDs separated by GRAPH_FIELD_SEP)
        already_source_ids.extend(split_string_by_multi_markers(already_node["source_id"], [GRAPH_FIELD_SEP]))  # 由此可见，实体来源分段是不唯一的，采用分隔符<SEP>隔开

        # 2.3. Split and collect existing file paths (multiple paths separated by GRAPH_FIELD_SEP)
        already_file_paths.extend(split_string_by_multi_markers(already_node["file_path"], [GRAPH_FIELD_SEP]))  # 由此可见，实体对应的原始文档路径是不唯一的，采用分隔符<SEP>隔开

        # 2.4. Collect existing description
        already_description.append(already_node["description"])  # 由此可见，实体描述是唯一的，这也是摘要处理后的结果所在

    # -- 合并处理【详细规则见注释】，得到最终的实体信息
    # 3. Merge and determine final entity properties

    # 3.1. Determine entity type by frequency count (most common type wins)
    entity_type = sorted(
        Counter([dp["entity_type"] for dp in nodes_data] + already_entity_types).items(),
        key=lambda x: x[1],
        reverse=True,
    )[0][0]  # 如果存在多个实体类型，则以出现次数多次为主

    # 3.2. Merge descriptions with field separator, sorted and deduplicated
    description = GRAPH_FIELD_SEP.join(sorted(set([dp["description"] for dp in nodes_data] + already_description)))  # 将所有实体描述用分隔符<SEP>拼接

    # 3.3. Merge source IDs, deduplicated
    source_id = GRAPH_FIELD_SEP.join(set([dp["source_id"] for dp in nodes_data] + already_source_ids))  # 将所有来源分段id用分隔符<SEP>拼接

    # 3.4. Merge file paths, deduplicated
    file_path = GRAPH_FIELD_SEP.join(set([dp["file_path"] for dp in nodes_data] + already_file_paths))  # 将所有来源原始文档路径用分隔符<SEP>拼接
    # -- 计算实体描述的数量【分隔符数量+1】、新实体描述去重后的数量
    # 4. Calculate description fragment counts for summarization decision
    num_fragment = description.count(GRAPH_FIELD_SEP) + 1  # Total description fragments
    num_new_fragment = len(set([dp["description"] for dp in nodes_data]))  # New unique descriptions
    # -- 如果存在多个实体描述，则基于llm进行摘要汇总操作
    # 5. Handle description summarization if there are multiple fragments
    if num_fragment > 1:
        # 5.1. Check if LLM summarization threshold is met
        if num_fragment >= force_llm_summary_on_merge:  # 实体描述数量超过【触发LLM摘要操作的阈值，默认10】阈值时，则基于llm进行摘要操作
            # 5.1.1. Log LLM summarization decision
            lightrag_logger.log_entity_merge(entity_name, num_fragment, num_new_fragment, is_llm_summary=True)

            # 5.1.2. Use LLM to summarize lengthy descriptions
            description = await _handle_entity_relation_summary(
                entity_name,  # 实体名称
                description,  # 实体描述【10个以上的实体描述】
                llm_model_func,  # llm操作
                tokenizer,  # 分词器
                llm_model_max_token_size,  # LLM输入的最大token数量
                summary_to_max_tokens,  # 摘要结果的最大token数量
                language,  # 语言
                lightrag_logger,  # lightrag日志实例
            )  # 基于llm对同一实体名称的多个实体描述做摘要总结
        else:  # 对于实体描述少于force_llm_summary_on_merge【10】个，不进行摘要总结【基于分隔符连接多个实体描述】
            # 5.2. Simple merge without LLM summarization (fragment count below threshold)
            lightrag_logger.log_entity_merge(entity_name, num_fragment, num_new_fragment, is_llm_summary=False)
    # -- 创建最终实体数据
    # 6. Create final node data structure
    node_data = dict(
        entity_id=entity_name,
        entity_type=entity_type,
        description=description,
        source_id=source_id,
        file_path=file_path,
        created_at=int(time.time()),
    )
    # -- 基于实体名称保存或更新实体数据
    # 7. Upsert the merged entity to knowledge graph
    await knowledge_graph_inst.upsert_node(
        entity_name,
        node_data=node_data,
    )
    # -- 补充实体名称字段并返回最终实体数据
    # 8. Add entity_name to returned data and return the final merged entity
    node_data["entity_name"] = entity_name
    return node_data


async def _merge_edges_then_upsert(
    src_id: str,
    tgt_id: str,
    edges_data: list[dict],
    knowledge_graph_inst: BaseGraphStorage,
    llm_model_func: callable,
    tokenizer: Tokenizer,
    llm_model_max_token_size: int,
    summary_to_max_tokens: int,
    language: str,
    force_llm_summary_on_merge: int,
    lightrag_logger: LightRAGLogger,
    workspace: str = "",
):  # 对同一起止实体的关系信息列表做合并【摘要】，得到为唯一的关系信息，并保存或更新到数据库，返回关系结构化信息
    if src_id == tgt_id:
        return None
    # -- 初始化各种已存在数据的变量
    already_weights = []  # 权重
    already_source_ids = []  # 关系来源分段id
    already_description = []  # 关系描述
    already_keywords = []  # 关系中的关键词
    already_file_paths = []  # 原始文档路径【这里对于多个文档的相同起止实体关系，会对其关系数据做合并摘要处理】【再次印证知识图谱是知识库维度的】
    # -- 基于当前起止实体名称检索属于当前关系的所有已存在关系数据 TODO 关键逻辑【跨文档、跨分段】
    if await knowledge_graph_inst.has_edge(src_id, tgt_id):
        already_edge = await knowledge_graph_inst.get_edge(src_id, tgt_id)  # 检索当前关系在数据库中已存在的关系数据
        # Handle the case where get_edge returns None or missing fields
        if already_edge:
            # Get weight with default 0.0 if missing
            already_weights.append(already_edge.get("weight", 0.0))  # 由此可见，关系权重是唯一的

            # Get source_id with empty string default if missing or None
            if already_edge.get("source_id") is not None:
                already_source_ids.extend(split_string_by_multi_markers(already_edge["source_id"], [GRAPH_FIELD_SEP]))  # 由此可见，关系来源分段id是不唯一的，采用分隔符<SEP>连接多个分段id

            # Get file_path with empty string default if missing or None
            if already_edge.get("file_path") is not None:
                already_file_paths.extend(split_string_by_multi_markers(already_edge["file_path"], [GRAPH_FIELD_SEP]))  # 由此可见，关系来源的原始文档路径是不唯一的，采用分隔符<SEP>连接多个原始文档路径

            # Get description with empty string default if missing or None
            if already_edge.get("description") is not None:
                already_description.append(already_edge["description"])  # 由此可见，关系描述是唯一的【通过llm摘要总结的结果】

            # Get keywords with empty string default if missing or None
            if already_edge.get("keywords") is not None:
                already_keywords.extend(split_string_by_multi_markers(already_edge["keywords"], [GRAPH_FIELD_SEP]))  # 由此可见，关系的关键字是不唯一的，采用采用分隔符<SEP>连接多个关键词
    # -- 汇总关系各种属性数据
    # Process edges_data with None checks
    weight = sum([dp["weight"] for dp in edges_data] + already_weights)  # 对于关系权重的更新采用累加规则
    description = GRAPH_FIELD_SEP.join(
        sorted(set([dp["description"] for dp in edges_data if dp.get("description")] + already_description))
    )  # 汇总关系描述【综合数据库已存在的关系描述和当前入参关系信息列表中的关系描述】，用分隔符<SEP>连接
    # 汇总关系关键词【去重收集数据库已存在的关系关键词和当前入参关系信息列表中的关系关键词】
    # Split all existing and new keywords into individual terms, then combine and deduplicate
    all_keywords = set()
    # Process already_keywords (which are comma-separated)
    for keyword_str in already_keywords:
        if keyword_str:  # Skip empty strings
            all_keywords.update(k.strip() for k in keyword_str.split(",") if k.strip())
    # Process new keywords from edges_data
    for edge in edges_data:
        if edge.get("keywords"):
            all_keywords.update(k.strip() for k in edge["keywords"].split(",") if k.strip())
    # Join all unique keywords with commas
    keywords = ",".join(sorted(all_keywords))

    source_id = GRAPH_FIELD_SEP.join(
        set([dp["source_id"] for dp in edges_data if dp.get("source_id")] + already_source_ids)
    )  # 汇总关系来源分段id
    file_path = GRAPH_FIELD_SEP.join(
        set([dp["file_path"] for dp in edges_data if dp.get("file_path")] + already_file_paths)
    )  # 汇总关系来源原始文件路径
    # -- 如果关系的起止实体不在数据库，则执行插入相应实体操作【实体描述，这里采用了关系的汇总描述】
    for need_insert_id in [src_id, tgt_id]:
        if not (await knowledge_graph_inst.has_node(need_insert_id)):
            await knowledge_graph_inst.upsert_node(
                need_insert_id,
                node_data={
                    "entity_id": need_insert_id,
                    "source_id": source_id,
                    "description": description,
                    "entity_type": "UNKNOWN",
                    "file_path": file_path,
                    "created_at": int(time.time()),
                },
            )
    # -- 对关系的所有描述进行摘要处理
    num_fragment = description.count(GRAPH_FIELD_SEP) + 1
    num_new_fragment = len(set([dp["description"] for dp in edges_data if dp.get("description")]))

    if num_fragment > 1:
        if num_fragment >= force_llm_summary_on_merge:  # 摘要处理的前提：当前关系的描述不少于force_llm_summary_on_merge【10】个
            lightrag_logger.log_relation_merge(src_id, tgt_id, num_fragment, num_new_fragment, is_llm_summary=True)

            description = await _handle_entity_relation_summary(
                f"({src_id}, {tgt_id})",
                description,
                llm_model_func,
                tokenizer,
                llm_model_max_token_size,
                summary_to_max_tokens,
                language,
                lightrag_logger,
            )  # 基于llm对同一关系的多个关系描述做摘要总结
        else:  # 对于少于force_llm_summary_on_merge【10】个的关系描述，不进行摘要总结【基于分隔符连接多个关系描述】
            lightrag_logger.log_relation_merge(src_id, tgt_id, num_fragment, num_new_fragment, is_llm_summary=False)
    # -- 创建最终关系数据，并保存或更新到数据库
    await knowledge_graph_inst.upsert_edge(
        src_id,
        tgt_id,
        edge_data=dict(
            weight=weight,
            description=description,
            keywords=keywords,
            source_id=source_id,
            file_path=file_path,
            created_at=int(time.time()),
        ),
    )
    # -- 构造并返回最终实体数据
    edge_data = dict(
        src_id=src_id,
        tgt_id=tgt_id,
        description=description,
        keywords=keywords,
        source_id=source_id,
        file_path=file_path,
        created_at=int(time.time()),
    )

    return edge_data


@timing_wrapper("merge_nodes_and_edges")
async def merge_nodes_and_edges(
    chunk_results: list,
    component: list[str],
    workspace: str,
    knowledge_graph_inst: BaseGraphStorage,
    entity_vdb: BaseVectorStorage,
    relationships_vdb: BaseVectorStorage,
    llm_model_func,
    tokenizer,
    llm_model_max_token_size,
    summary_to_max_tokens,
    addon_params,
    force_llm_summary_on_merge,
    lightrag_logger: LightRAGLogger,
) -> dict[str, int]:  # 对单个文档的单个连通组件，合并实体关系，返回最终保存的实体数量和关系数量【保存形式：节点表、边表、实体向量表、关系向量表】
    # Now using fine-grained locking inside _merge_nodes_and_edges_impl
    return await _merge_nodes_and_edges_impl(
        chunk_results,
        workspace,
        knowledge_graph_inst,
        entity_vdb,
        relationships_vdb,
        llm_model_func,
        tokenizer,
        llm_model_max_token_size,
        summary_to_max_tokens,
        addon_params,
        force_llm_summary_on_merge,
        lightrag_logger,
    )


async def _merge_nodes_and_edges_impl(
    chunk_results: list,  # 元组列表，当前连通组件对应的实体关系数据列表，形如[(分段1的属于当前连通组件的实体数据【字典，形如：{实体1：实体1数据}】，分段1的属于当前连通组件的关系数据【字典，形如：{(起始实体1，目标实体1)：对应边数据}】)]
    workspace: str,  # 知识库id
    knowledge_graph_inst: BaseGraphStorage,  # 知识图谱存储实例，见aperag.graph.lightrag.kg.pg_ops_sync_graph_storage.PGOpsSyncGraphStorage
    entity_vdb: BaseVectorStorage,  # 实体存储实例，见aperag.graph.lightrag.kg.pg_ops_sync_vector_storage.PGOpsSyncVectorStorage
    relationships_vdb: BaseVectorStorage,  # 关系存储实例，见aperag.graph.lightrag.kg.pg_ops_sync_vector_storage.PGOpsSyncVectorStorage
    llm_model_func,  # llm操作定义
    tokenizer,  # 分词器实例【TiktokenTokenizer(gpt-4o-mini)】
    llm_model_max_token_size,  # 大模型输入token的数量
    summary_to_max_tokens,  # 生成摘要的最大token数量，默认500
    addon_params,  # lightrag附加参数：{"language": "The same language like input text"}
    force_llm_summary_on_merge,  # 触发LLM摘要的阈值，默认10个
    lightrag_logger: LightRAGLogger,  # lightrag日志实例
) -> dict[str, int]:  # 合并实体关系【单个文档的单个连通组件】，返回最终保存的实体数量和关系数量【保存形式：节点表、边表、实体向量表、关系向量表】
    """Internal implementation of merge_nodes_and_edges with fine-grained locking"""

    # Extract language from addon_params
    language = addon_params.get("language", "English")  # 获取语言参数

    # Collect all nodes and edges from all chunks
    all_nodes = defaultdict(list)  # 初始化【最终】实体信息【字典，形如：{实体名称：实体信息列表}】
    all_edges = defaultdict(list)  # 初始化【最终】关系信息【字典，形如：{有向元组（起始实体，终止实体）：关系信息列表}】
    # -- 初始收集实体和关系【基于排序，统一关系的表示形式，例如a->b与b->a，统一用a->b表示】
    for maybe_nodes, maybe_edges in chunk_results:
        # Collect nodes
        for entity_name, entities in maybe_nodes.items():
            all_nodes[entity_name].extend(entities)

        # Collect edges with sorted keys for undirected graph
        for edge_key, edges in maybe_edges.items():
            sorted_edge_key = tuple(sorted(edge_key))  # 有向元组？对于无向图，用以统一边的表示形式，消除顺序差异带来的影响
            all_edges[sorted_edge_key].extend(edges)
    # -- 基于细粒度锁【线程锁】处理实体信息【针对同一实体名称的多个实体信息及数据库中已存在的实体信息做摘要总结，保存或更新，并对实体内容【实体名称\n最终实体描述】做embedding处理并保存或更新】
    # Process entities with fine-grained locking
    entity_count = 0

    for entity_name, entities in all_nodes.items():
        # Create lock for this specific entity
        entity_lock = get_or_create_lock(f"entity:{entity_name}:{workspace}")  # 基于当前实体名称和知识库id，创建锁

        async with entity_lock:  # 锁保证了实体的逐个处理
            # Process and update entity in graph db
            entity_data = await _merge_nodes_then_upsert(
                entity_name,  # 实体名称
                entities,  # 当前实体名称对应的实体信息列表
                knowledge_graph_inst,  # 知识图谱存储实例，见aperag.graph.lightrag.kg.pg_ops_sync_graph_storage.PGOpsSyncGraphStorage
                llm_model_func,  # llm操作，用于对实体信息列表做合并摘要
                tokenizer,  # 分词器实例【TiktokenTokenizer(gpt-4o-mini)】
                llm_model_max_token_size,  # 大模型输入token的最大数量
                summary_to_max_tokens,  # 生成摘要【合并总结】的最大token数量，默认500
                language,  # Pass language instead of addon_params  lightrag附加参数：{"language": "The same language like input text"}
                force_llm_summary_on_merge,  # 触发LLM摘要的阈值，默认10个
                lightrag_logger,  # lightrag日志实例
                workspace,  # 知识库id
            )  # 对同一实体名称的实体信息列表做合并【摘要】，并保存或更新到数据库【表名：lightrag_graph_nodes】，返回实体结构化信息

            # Update entity in vector db immediately under the same lock
            if entity_vdb is not None and entity_data:
                vdb_data = {
                    compute_mdhash_id(entity_data["entity_name"], prefix="ent-", workspace=workspace): {
                        "entity_name": entity_data["entity_name"],
                        "entity_type": entity_data["entity_type"],
                        "content": f"{entity_data['entity_name']}\n{entity_data['description']}",
                        "source_id": entity_data["source_id"],
                        "file_path": entity_data.get("file_path", "unknown_source"),
                    }
                }
                # 保存或更新向量库中的实体信息【将实体数据【分批embedding处理后，这里是单个实体】保存或更新至数据库【表名：lightrag_vdb_entity】】
                await entity_vdb.upsert(vdb_data)  # 实体存储实例，见aperag.graph.lightrag.kg.pg_ops_sync_vector_storage.PGOpsSyncVectorStorage

            entity_count += 1  # 最终实体数量加1
    # -- 基于细粒度锁【线程锁】处理关系信息【针对同一起止实体的多个关系信息及数据库中已存在的关系信息做摘要总结，保存或更新，并对关系内容【起止实体名称\n最终关系描述】做embedding处理并保存或更新】
    # Process relationships with fine-grained locking
    relation_count = 0

    for edge_key, edges in all_edges.items():
        # Create lock for this specific relationship
        # Sort edge key to ensure consistent lock naming
        sorted_edge_key = tuple(sorted(edge_key))  # 前面在收集all_edges的过程中，已经对起止实体元组排序过了，以消除两个实体因顺序导致的差异【认为两个实体的关系不因其顺序不同而不同】
        relationship_lock = get_or_create_lock(f"relationship:{sorted_edge_key[0]}:{sorted_edge_key[1]}:{workspace}")  # 基于当前关系的起止实体名称和知识库id，创建锁

        async with relationship_lock:
            # Process and update relationship in graph db
            edge_data = await _merge_edges_then_upsert(
                edge_key[0],  # 起始实体名称
                edge_key[1],  # 目标实体名称
                edges,  # 当前起止实体对应的关系信息列表
                knowledge_graph_inst,  # 知识图谱存储实例，见aperag.graph.lightrag.kg.pg_ops_sync_graph_storage.PGOpsSyncGraphStorage
                llm_model_func,
                tokenizer,
                llm_model_max_token_size,
                summary_to_max_tokens,
                language,  # Pass language instead of addon_params
                force_llm_summary_on_merge,
                lightrag_logger,
                workspace,
            )  # 对同一起止实体的关系信息列表做合并【摘要】，并保存或更新到数据库【表名：lightrag_graph_edges】，返回关系结构化信息

            # Update relationship in vector db immediately under the same lock
            if relationships_vdb is not None and edge_data is not None:
                vdb_data = {
                    compute_mdhash_id(edge_data["src_id"] + edge_data["tgt_id"], prefix="rel-", workspace=workspace): {
                        "src_id": edge_data["src_id"],
                        "tgt_id": edge_data["tgt_id"],
                        "keywords": edge_data["keywords"],
                        "content": f"{edge_data['src_id']}\t{edge_data['tgt_id']}\n{edge_data['keywords']}\n{edge_data['description']}",
                        "source_id": edge_data["source_id"],
                        "file_path": edge_data.get("file_path", "unknown_source"),
                    }
                }
                # 保存或更新向量库中的关系信息【将关系数据【分批embedding处理后，这里是单个关系】保存或更新至数据库【表名：lightrag_vdb_relation】】
                await relationships_vdb.upsert(vdb_data)  # 实体存储实例，见aperag.graph.lightrag.kg.pg_ops_sync_vector_storage.PGOpsSyncVectorStorage

            if edge_data is not None:
                relation_count += 1  # 最终关系数量加1

    return {"entity_count": entity_count, "relation_count": relation_count}  # 返回最终保存的实体数量和关系数量


@timing_wrapper("extract_entities")
async def extract_entities(
    chunks: dict[str, TextChunkSchema],
    use_llm_func: callable,
    entity_extract_max_gleaning: int,
    addon_params: dict,
    llm_model_max_async: int,
    lightrag_logger: LightRAGLogger,
) -> list:  # 对分段数据【多个分段，字典形式{分段id：单个分段数据详情}】提取实体和关系，结果形如：[分段1的实体关系信息【形如：{实体名称1：实体名称1的实体信息列表}， {(源实体名称1，目标实体名称1)：相应起止实体名称的边信息列表}】]
    # -- 重构分段数据为元组列表，每个元组(分段id, 单个分段数据详情)对应单个分段数据
    ordered_chunks = list(chunks.items())  # 将键值对“分段id：单个分段数据详情”转化为元组(分段id, 单个分段数据详情)，构成元组列表
    # -- 获取实体提取所需参数【语言、实体类型、示例】
    # add language and example number params to prompt
    language = addon_params.get("language", PROMPTS["DEFAULT_LANGUAGE"])  # 语言，对于当前lightrag，该值为“The same language like input text”
    entity_types = addon_params.get("entity_types", PROMPTS["DEFAULT_ENTITY_TYPES"])  # 实体类型，采用默认设置：organization/person/geo/event/product/technology/date/category
    example_number = addon_params.get("example_number", None)  # 示例个数，对于当前lightrag，该值为none
    if example_number and example_number < len(PROMPTS["entity_extraction_examples"]):
        examples = "\n".join(PROMPTS["entity_extraction_examples"][: int(example_number)])
    else:  # 对于当前lightrag，采用所有示例
        examples = "\n".join(PROMPTS["entity_extraction_examples"])
    # -- 收集示例中的占位符相关配置信息，以完善示例内容。观察aperag/graph/lightrag/prompt.py中关于示例的配置可知，其中存在各种占位符【{tuple_delimiter}、{record_delimiter}、{completion_delimiter}】
    example_context_base = dict(
        tuple_delimiter=PROMPTS["DEFAULT_TUPLE_DELIMITER"],  # 元组分隔符"<|>"
        record_delimiter=PROMPTS["DEFAULT_RECORD_DELIMITER"],  # 记录分隔符"##"
        completion_delimiter=PROMPTS["DEFAULT_COMPLETION_DELIMITER"],  # 完成分隔符"<|COMPLETE|>"
        entity_types=", ".join(entity_types),  # 实体类型"organization, person, geo, event, product, technology, date, category"【用于实体提取】
        language=language,  # 语言"The same language like input text"【用于实体提取和实体摘要描述】
    )
    # add example's format
    examples = examples.format(**example_context_base)  # 将示例内容中的占位符替换为相应配置内容
    # -- 收集实体提取prompt中的占位符相关配置信息，以完善实体提取prompt、继续进行实体提取prompt。
    entity_extract_prompt = PROMPTS["entity_extraction"]
    context_base = dict(
        tuple_delimiter=PROMPTS["DEFAULT_TUPLE_DELIMITER"],
        record_delimiter=PROMPTS["DEFAULT_RECORD_DELIMITER"],
        completion_delimiter=PROMPTS["DEFAULT_COMPLETION_DELIMITER"],
        entity_types=",".join(entity_types),
        examples=examples,  # 示例内容作为实体提取prompt的一部分
        language=language,
    )

    continue_prompt = PROMPTS["entity_continue_extraction"].format(**context_base)
    if_loop_prompt = PROMPTS["entity_if_loop_extraction"]  # 判断是否需要循环提取实体【也即判断是否存在尚未提取的实体】
    # -- 进行实体和关系提取操作，并记录已处理的分段数量
    processed_chunks = 0
    total_chunks = len(ordered_chunks)

    async def _process_extraction_result(result: str, chunk_key: str, file_path: str = "unknown_source"):  # 解析大模型的实体关系提取结果【实体和关系】
        """Process a single extraction result (either initial or gleaning)
        Args:
            result (str): The extraction result to process  大模型输出结果【分段中的实体和关系信息】
            chunk_key (str): The chunk key for source tracking  分段id
            file_path (str): The file path for citation  原始文档路径
        Returns:
            tuple: (nodes_dict, edges_dict) containing the extracted entities and relationships
        """
        maybe_nodes = defaultdict(list)  # 一个实体名称，可能对应多种实体类型及相应的实体描述
        maybe_edges = defaultdict(list)  # 一条边，可能对应多种关系描述
        """
        单个record形如：
        ("entity"<|>"Alex"<|>"person"<|>"Alex is a character who experiences frustration and is observant of the dynamics among other characters.")
        或者
        ("relationship"<|>"Alex"<|>"Taylor"<|>"Alex is affected by Taylor's authoritarian certainty and observes changes in Taylor's attitude towards the device."<|>"power dynamics, perspective shift"<|>7)
        """
        records = split_string_by_multi_markers(
            result,
            [context_base["record_delimiter"], context_base["completion_delimiter"]],
        )  # 基于记录分隔符和完成分隔符将大模型输出结果分割，得到非空文本段列表

        for record in records:
            record = re.search(r"\((.*)\)", record)  # 匹配英文小括号里面的内容，形如“(abc)”--“abc”
            if record is None:
                continue
            record = record.group(1)  # 获取匹配中的文本，也即“(abc)”--“abc”中的abc
            """
            基于元组分隔符分割后的结果形如：
            ["entity", "Alex", "person", "Alex is a character who experiences frustration and is observant of the dynamics among other characters."]
            实体信息组成模式：[实体标识【entity】，实体名称，实体类型，实体描述]
            或者
            ["relationship", "Alex", "Taylor", "Alex is affected by Taylor's authoritarian certainty and observes changes in Taylor's attitude towards the device.", "power dynamics, perspective shift", 7]
            关系信息组成模式：[关系标识【relationship】，源实体名称，目标实体名称，关系描述，关系关键词，权重]
            """
            record_attributes = split_string_by_multi_markers(record, [context_base["tuple_delimiter"]])  # 基于元组分隔符进行分割，得到非空文本段列表

            if_entities = await _handle_single_entity_extraction(record_attributes, chunk_key, file_path)  # 提取实体，字典形式【内含：实体名称、实体类型、实体描述、分段id和原始文档路径】
            if if_entities is not None:
                maybe_nodes[if_entities["entity_name"]].append(if_entities)  # 收集实体信息，键值对形式，形如“实体名称：[当前实体信息]”
                continue

            if_relation = await _handle_single_relationship_extraction(record_attributes, chunk_key, file_path)  # 提取关系，字典形式【内含：源节点id【源实体名称】、目标节点id【目标实体名称】、权重、边描述【关系描述】、边关键词【关系关键词】、来源id【分段id】、原始文档路径】
            if if_relation is not None:
                maybe_edges[(if_relation["src_id"], if_relation["tgt_id"])].append(if_relation)  # 收集实体信息，键值对形式，形如“(源实体名称，目标实体名称)：[当前边信息]”

        return maybe_nodes, maybe_edges

    async def _process_single_content(chunk_key_dp: tuple[str, TextChunkSchema]):  # 对单个分段进行实体和关系提取
        """Process a single chunk
        Args:
            chunk_key_dp (tuple[str, TextChunkSchema]):
                ("chunk-xxxxxx", {"tokens": int, "content": str, "full_doc_id": str, "chunk_order_index": int})
        Returns:
            tuple: (maybe_nodes, maybe_edges) containing extracted entities and relationships
        """
        nonlocal processed_chunks  # 声明非局部变量，记录已经处理过的分段数量
        chunk_key = chunk_key_dp[0]  # 分段id
        chunk_dp = chunk_key_dp[1]  # 分段数据详情【分段内容，分段长度，分段在整个markdown文本中的索引顺序，原始文档id，原始文档路径】
        content = chunk_dp["content"]  # 分段内容
        # Get file path from chunk data or use default
        file_path = chunk_dp.get("file_path", "unknown_source")  # 原始文档路径

        # Get initial extraction
        hint_prompt = entity_extract_prompt.format(**{**context_base, "input_text": content})  # 基于分段内容和context_base填充实体提取prompt
        """
        模型输出形如：
        ("entity"<|>"Alex"<|>"person"<|>"Alex is a character who experiences frustration and is observant of the dynamics among other characters.")##
        ("relationship"<|>"Alex"<|>"Taylor"<|>"Alex is affected by Taylor's authoritarian certainty and observes changes in Taylor's attitude towards the device."<|>"power dynamics, perspective shift"<|>7)##
        """
        final_result = await use_llm_func(hint_prompt)  # 大模型处理
        """
        history形如：[
            {"role": user, "content": 输入提示词},
            {"role": assistant, "content": 模型输出}
        ]
        """
        history = pack_user_ass_to_openai_messages(hint_prompt, final_result)  # 基于输入提示词和模型输出构造openai格式的消息列表

        # Process initial extraction with file path
        maybe_nodes, maybe_edges = await _process_extraction_result(final_result, chunk_key, file_path)  # 解析模型处理结果，获取可能的实体【节点】和关系【边】

        # Process additional gleaning results
        for now_glean_index in range(entity_extract_max_gleaning):  # 对不明确的内容尝试提取实体的最大次数【当前lightrag中默认0次，因此这里不执行】
            glean_result = await use_llm_func(continue_prompt, history_messages=history)  # 基于对话历史【已含有分段信息和已经输出的实体及关系信息，因此这里不需要再设置分段信息】和继续提取实体提示词，尝试再次提取遗漏的实体或关系

            history += pack_user_ass_to_openai_messages(continue_prompt, glean_result)

            # Process gleaning result separately with file path
            glean_nodes, glean_edges = await _process_extraction_result(glean_result, chunk_key, file_path)
            # 将继续提取的实体和关系结果合并到第一次提取的实体和关系结果中
            # Merge results - only add entities and edges with new names
            for entity_name, entities in glean_nodes.items():
                if entity_name not in maybe_nodes:  # Only accetp entities with new name in gleaning stage
                    maybe_nodes[entity_name].extend(entities)
            for edge_key, edges in glean_edges.items():
                if edge_key not in maybe_edges:  # Only accetp edges with new name in gleaning stage
                    maybe_edges[edge_key].extend(edges)

            if now_glean_index == entity_extract_max_gleaning - 1:  # 对不明确的内容尝试提取实体的最大次数已经用完了，直接跳出
                break

            if_loop_result: str = await use_llm_func(if_loop_prompt, history_messages=history)  # 基于当前最新对话历史，让大模型判断是否还存在继续提取的可能性，也即是否还需要继续提取
            if_loop_result = if_loop_result.strip().strip('"').strip("'").lower()
            if if_loop_result != "yes":  # 如果大模型认为不需要继续提取，则直接跳出
                break

        processed_chunks += 1  # 已处理的分段数量加1
        entities_count = len(maybe_nodes)
        relations_count = len(maybe_edges)

        lightrag_logger.log_extraction_progress(processed_chunks, total_chunks, entities_count, relations_count)  # 打印实体和关系提取情况

        # Return the extracted nodes and edges for centralized processing
        return maybe_nodes, maybe_edges  # 返回实体【节点】和关系【边】
    # ---- TODO 异步I/O密集型任务[这里指远程调用大模型实现提取实体关系]的并发控制实现。核心逻辑是控制异步任务的最大并发数，确保任务有序执行并妥善处理可能的异常。
    # Get max async tasks limit
    """
    信号量作用：Semaphore(n) 表示最多允许 n 个任务同时执行。当调用 async with semaphore 时，任务会尝试获取 “许可证”：
        若当前并发数 < llm_model_max_async，直接执行；
        若已达上限，任务会阻塞等待，直到其他任务完成并释放 “许可证”。
        
    目的：防止并发任务过多导致的资源耗尽（如 API 调用频率超限、内存占用过高等）。
    """
    semaphore = asyncio.Semaphore(llm_model_max_async)  # 初始化信号量【类似“并发许可证”】，限制最大并发任务数为 llm_model_max_async

    async def _process_with_semaphore(chunk):
        async with semaphore:  # 进入上下文时获取“许可证”，超出限制则等待
            return await _process_single_content(chunk)  # 执行实际处理
    # ---- 创建并发任务列表
    """
    遍历 ordered_chunks 中的每个元素 c，为其创建一个异步任务。
    所有任务会被添加到 tasks 列表中，等待统一调度。
    注意：create_task 会立即将任务加入事件循环，但实际执行会受信号量【并发许可证】限制（不会立即全部执行，受最大并发数制约）。
    """
    tasks = []
    for c in ordered_chunks:  # 逐个分段提取实体和关系
        task = asyncio.create_task(_process_with_semaphore(c))  # 为每个 chunk 创建异步任务，任务函数是 _process_with_semaphore
        tasks.append(task)
    # ---- 等待任务执行：优先处理第一个异常
    """
    等待任务完成，当出现第一个异常时立即返回（不再等待其他任务）
    
    asyncio.wait 用于等待多个任务的结果，return_when=asyncio.FIRST_EXCEPTION 是关键参数：
        - 正常情况下【未设置return_when=asyncio.FIRST_EXCEPTION】，等待所有任务完成，返回 done（已完成的任务）和 pending（未完成的任务）。
        - 当前设置：若任何一个任务抛出异常，会立即返回，此时 done 包含已完成（或抛出异常）的任务，pending 包含未完成的任务。
    
    目的：快速响应异常，避免无效等待（一旦有任务失败，后续任务无需继续执行）。

    """
    # Wait for tasks to complete or for the first exception to occur
    # This allows us to cancel remaining tasks if any task fails
    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)
    # ---- 异常处理：终止所有任务并传播异常
    """    
    核心逻辑：一旦发现任何任务失败（抛出异常），立即终止所有未完成的任务，并将异常向上传播。
    
    为什么要取消 pending 任务？
    避免资源浪费：既然整个流程因某个任务失败而需要终止，剩余任务的执行已无意义，及时取消可释放资源（如网络连接、内存等）。
    """
    # Check if any task raised an exception
    for task in done:
        if task.exception():  # 检查已完成的任务是否有异常，若有异常
            # If a task failed, cancel all pending tasks
            # This prevents unnecessary processing since the parent function will abort anyway
            for pending_task in pending:  # 取消所有未完成的任务（避免继续消耗资源）
                pending_task.cancel()

            # Wait for cancellation to complete
            # 等待所有被取消的任务彻底终止
            if pending:
                await asyncio.wait(pending)
            # # 重新抛出异常，让调用方知道任务失败
            # Re-raise the exception to notify the caller
            raise task.exception()
    # ---- 收集结果：所有任务成功时汇总结果
    """
    当 done 中的所有任务都无异常时，说明全部处理完成。
    通过 task.result() 获取每个任务的返回值，组合成 chunk_results 列表返回。
    """
    # If all tasks completed successfully, collect results
    chunk_results = [task.result() for task in tasks]

    # Return the chunk_results for later processing in merge_nodes_and_edges
    return chunk_results  # 实体和关系


async def build_query_context(
    query: str,  # 用户问题
    knowledge_graph_inst: BaseGraphStorage,  # 知识图谱存储实例
    entities_vdb: BaseVectorStorage,  # 实体向量存储实例
    relationships_vdb: BaseVectorStorage,  # 关系向量存储实例
    text_chunks_db: BaseKVStorage,  # 分段内容存储实例
    query_param: QueryParam,  # 检索参数：是否仅需内容、top_k、检索模式
    tokenizer: Tokenizer,
    llm_model_func: callable,
    addon_params: dict,
    chunks_vdb: BaseVectorStorage = None,  # 分段向量存储实例
):  # 知识图谱检索算法
    # -- llm选择
    if query_param.model_func:
        use_model_func = query_param.model_func
    else:
        use_model_func = llm_model_func
    # -- 提取用户问题中的高低级别关键词
    # 高级关键字侧重于总体概念或主题，而低级关键字侧重于特定实体、细节或具体术语
    hl_keywords, ll_keywords = await get_keywords_from_query(
        query, query_param, tokenizer, use_model_func, addon_params
    )  # 对用户问题提取关键词【如果检索参数中存在关键词，则取之；反之，则使用llm从用户问题中提取关键词】

    logger.debug(f"High-level keywords: {hl_keywords}")
    logger.debug(f"Low-level  keywords: {ll_keywords}")
    # 处理空关键词情况
    # Handle empty keywords
    if hl_keywords == [] and ll_keywords == []:  # 高低级别关键词皆为空，直接返回'fail_response'
        logger.warning("low_level_keywords and high_level_keywords is empty")
        return PROMPTS["fail_response"]
    if ll_keywords == [] and query_param.mode in ["local", "hybrid"]:  # 低级别关键词为空，且mode参数为local或hybrid，则设置mode为global
        logger.warning(
            "low_level_keywords is empty, switching from %s mode to global mode",
            query_param.mode,
        )
        query_param.mode = "global"
    if hl_keywords == [] and query_param.mode in ["global", "hybrid"]:  # 高级别关键词为空，且mode参数为global或hybrid，则设置mode为local
        logger.warning(
            "high_level_keywords is empty, switching from %s mode to local mode",
            query_param.mode,
        )
        query_param.mode = "local"
    # 拼接关键词
    ll_keywords_str = ", ".join(ll_keywords) if ll_keywords else ""
    hl_keywords_str = ", ".join(hl_keywords) if hl_keywords else ""

    # Build context
    return await _build_query_context_from_keywords(
        ll_keywords_str,  # 低级别关键词
        hl_keywords_str,  # 高级别关键词
        knowledge_graph_inst,  # 知识图谱存储实例
        entities_vdb,  # 实体向量存储实例
        relationships_vdb,  # 关系向量存储实例
        text_chunks_db,  # 分段内容存储实例
        query_param,  # 检索参数
        tokenizer,  # 分词器
        chunks_vdb,  # 分段向量存储实例
    )  # 知识图谱数据检索


async def kg_query(
    query: str,
    knowledge_graph_inst: BaseGraphStorage,
    entities_vdb: BaseVectorStorage,
    relationships_vdb: BaseVectorStorage,
    text_chunks_db: BaseKVStorage,
    query_param: QueryParam,
    tokenizer: Tokenizer,
    llm_model_func: callable,
    addon_params: dict,
    system_prompt: str | None = None,
    chunks_vdb: BaseVectorStorage = None,
) -> str | AsyncIterator[str]:
    if query_param.model_func:
        use_model_func = query_param.model_func
    else:
        use_model_func = llm_model_func

    # Build context
    entities_context, relations_context, text_units_context = await build_query_context(
        query,
        knowledge_graph_inst,
        entities_vdb,
        relationships_vdb,
        text_chunks_db,
        query_param,
        tokenizer,
        llm_model_func,
        addon_params,
        chunks_vdb,
    )

    # 转换为 JSON 字符串
    entities_str = json.dumps(entities_context, ensure_ascii=False)
    relations_str = json.dumps(relations_context, ensure_ascii=False)
    text_units_str = json.dumps(text_units_context, ensure_ascii=False)

    context = f"""-----Entities(KG)-----

    ```json
    {entities_str}
    ```

    -----Relationships(KG)-----

    ```json
    {relations_str}
    ```

    -----Document Chunks(DC)-----

    ```json
    {text_units_str}
    ```

    """

    if query_param.only_need_context:
        return context
    if context is None:
        return PROMPTS["fail_response"]

    # Process conversation history
    history_context = ""
    if query_param.conversation_history:
        history_context = get_conversation_turns(query_param.conversation_history, query_param.history_turns)

    # Build system prompt
    user_prompt = query_param.user_prompt if query_param.user_prompt else PROMPTS["DEFAULT_USER_PROMPT"]
    sys_prompt_temp = system_prompt if system_prompt else PROMPTS["rag_response"]
    sys_prompt = sys_prompt_temp.format(
        context_data=context,
        response_type=query_param.response_type,
        history=history_context,
        user_prompt=user_prompt,
    )

    if query_param.only_need_prompt:
        return sys_prompt

    len_of_prompts = len(tokenizer.encode(query + sys_prompt))
    logger.debug(f"[kg_query]Prompt Tokens: {len_of_prompts}")

    response = await use_model_func(
        query,
        system_prompt=sys_prompt,
        stream=query_param.stream,
    )
    if isinstance(response, str) and len(response) > len(sys_prompt):
        response = (
            response.replace(sys_prompt, "")
            .replace("user", "")
            .replace("model", "")
            .replace(query, "")
            .replace("<system>", "")
            .replace("</system>", "")
            .strip()
        )

    return response


async def get_keywords_from_query(
    query: str,  # 用户问题
    query_param: QueryParam,  # 检索参数
    tokenizer: Tokenizer,
    llm_model_func: callable,
    addon_params: dict,
) -> tuple[list[str], list[str]]:  # 提取用户问题中的关键词【如果检索参数中存在关键词，则取之；反之，则使用llm从用户问题中提取关键词】
    """
    由PROMPTS["keywords_extraction"]中高低级别关键词的定义可知：高级关键字侧重于总体概念或主题，而低级关键字侧重于特定实体、细节或具体术语
    """
    """
    Retrieves high-level and low-level keywords for RAG operations.

    This function checks if keywords are already provided in query parameters,
    and if not, extracts them from the query text using LLM.

    Returns:
        A tuple containing (high_level_keywords, low_level_keywords)
    """
    # Check if pre-defined keywords are already provided
    if query_param.hl_keywords or query_param.ll_keywords:
        return query_param.hl_keywords, query_param.ll_keywords

    # Extract keywords using extract_keywords_only function which already supports conversation history
    hl_keywords, ll_keywords = await extract_keywords_only(query, query_param, tokenizer, llm_model_func, addon_params)
    return hl_keywords, ll_keywords


async def extract_keywords_only(
    text: str,
    param: QueryParam,
    tokenizer: Tokenizer,
    llm_model_func: callable,
    addon_params: dict,
) -> tuple[list[str], list[str]]:  # 使用llm从用户问题中提取关键词
    """
    Extract high-level and low-level keywords from the given 'text' using the LLM.
    This method does NOT build the final RAG context or provide a final answer.
    It ONLY extracts keywords (hl_keywords, ll_keywords).
    """
    # 2. Build the examples
    example_number = addon_params.get("example_number", None)
    if example_number and example_number < len(PROMPTS["keywords_extraction_examples"]):
        examples = "\n".join(PROMPTS["keywords_extraction_examples"][: int(example_number)])
    else:
        examples = "\n".join(PROMPTS["keywords_extraction_examples"])
    language = addon_params.get("language", PROMPTS["DEFAULT_LANGUAGE"])

    # 3. Process conversation history
    history_context = ""
    if param.conversation_history:
        history_context = get_conversation_turns(param.conversation_history, param.history_turns)

    # 4. Build the keyword-extraction prompt
    kw_prompt = PROMPTS["keywords_extraction"].format(
        query=text, examples=examples, language=language, history=history_context
    )  # 由提示词中对于高低级别关键词的定义可知：高级关键字侧重于总体概念或主题，而低级关键字侧重于特定实体、细节或具体术语

    len_of_prompts = len(tokenizer.encode(kw_prompt))
    logger.debug(f"[kg_query]Prompt Tokens: {len_of_prompts}")

    # 5. Call the LLM for keyword extraction
    if param.model_func:
        use_model_func = param.model_func
    else:
        use_model_func = llm_model_func

    result = await use_model_func(kw_prompt, keyword_extraction=True)

    # 6. Parse out JSON from the LLM response
    match = re.search(r"\{.*\}", result, re.DOTALL)
    if not match:
        logger.error("No JSON-like structure found in the LLM respond.")
        return [], []
    try:
        keywords_data = json.loads(match.group(0))
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}")
        return [], []

    hl_keywords = keywords_data.get("high_level_keywords", [])
    ll_keywords = keywords_data.get("low_level_keywords", [])

    return hl_keywords, ll_keywords


async def _get_vector_context(
    query: str,
    chunks_vdb: BaseVectorStorage,
    query_param: QueryParam,
    tokenizer: Tokenizer,
) -> tuple[list, list, list] | None:
    """
    Retrieve vector context from the vector database.

    This function performs vector search to find relevant text chunks for a query,
    formats them with file path and creation time information.

    Args:
        query: The query string to search for
        chunks_vdb: Vector database containing document chunks
        query_param: Query parameters including top_k and ids
        tokenizer: Tokenizer for counting tokens

    Returns:
        Tuple (empty_entities, empty_relations, text_units) for combine_contexts,
        compatible with _get_edge_data and _get_node_data format
    """
    try:
        results = await chunks_vdb.query(query, top_k=query_param.top_k, ids=query_param.ids)
        if not results:
            return [], [], []

        valid_chunks = []
        for result in results:
            if "content" in result:
                # Directly use content from chunks_vdb.query result
                chunk_with_time = {
                    "content": result["content"],
                    "created_at": result.get("created_at", None),
                    "file_path": result.get("file_path", "unknown_source"),
                }
                valid_chunks.append(chunk_with_time)

        if not valid_chunks:
            return [], [], []

        maybe_trun_chunks = truncate_list_by_token_size(
            valid_chunks,
            key=lambda x: x["content"],
            max_token_size=query_param.max_token_for_text_unit,
            tokenizer=tokenizer,
        )

        logger.debug(
            f"Truncate chunks from {len(valid_chunks)} to {len(maybe_trun_chunks)} (max tokens:{query_param.max_token_for_text_unit})"
        )
        logger.info(f"Vector query: {len(maybe_trun_chunks)} chunks, top_k: {query_param.top_k}")

        if not maybe_trun_chunks:
            return [], [], []

        # Create empty entities and relations contexts
        entities_context = []
        relations_context = []

        # Create text_units_context directly as a list of dictionaries
        text_units_context = []
        for i, chunk in enumerate(maybe_trun_chunks):
            text_units_context.append(
                {
                    "id": i + 1,
                    "content": chunk["content"],
                    "file_path": chunk["file_path"],
                }
            )

        return entities_context, relations_context, text_units_context
    except Exception as e:
        logger.error(f"Error in _get_vector_context: {e}")
        return [], [], []


async def _build_query_context_from_keywords(
    ll_keywords: str,  # 低级别关键词
    hl_keywords: str,  # 高级别关键词
    knowledge_graph_inst: BaseGraphStorage,  # 知识图谱存储实例
    entities_vdb: BaseVectorStorage,  # 实体向量存储实例
    relationships_vdb: BaseVectorStorage,  # 关系向量存储实例
    text_chunks_db: BaseKVStorage,  # 分段内容存储实例
    query_param: QueryParam,  # 检索参数
    tokenizer: Tokenizer,  # 分词器
    chunks_vdb: BaseVectorStorage = None,  # Add chunks_vdb parameter for mix mode 分段向量存储实例
):  # 知识图谱数据检索逻辑
    """
    检索模式分为四种：
        local：
            对低级别关键词，基于embedding相似度机制检索节点数据
        global：
            对高级别关键词，基于embedding相似度机制检索边数据
        hybrid：
            对低级别关键词，基于embedding相似度机制检索节点数据
            对高级别关键词，基于embedding相似度机制检索边数据
            去重合并
        mix：
            对低级别关键词，基于embedding相似度机制检索节点数据
            对高级别关键词，基于embedding相似度机制检索边数据
            对用户原始问题，基于embedding相似度机制检索分段数据
            去重合并
    """
    logger.info(f"Process {os.getpid()} building query context...")

    # Handle local and global modes as before
    if query_param.mode == "local":
        entities_context, relations_context, text_units_context = await _get_node_data(
            ll_keywords,  # 低级别关键词【非空】
            knowledge_graph_inst,
            entities_vdb,
            text_chunks_db,
            query_param,
            tokenizer,
        )  # 检索节点数据
    elif query_param.mode == "global":
        entities_context, relations_context, text_units_context = await _get_edge_data(
            hl_keywords,  # 高级别关键词【非空】
            knowledge_graph_inst,
            relationships_vdb,
            text_chunks_db,
            query_param,
            tokenizer,
        )  # 检索边数据
    else:  # hybrid or mix mode 混合检索模式，基于低级别关键词检索节点数据，基于高级别关键词检索边数据，若为mix模式则基于原始问题检索分段数据
        ll_data = await _get_node_data(
            ll_keywords,
            knowledge_graph_inst,
            entities_vdb,
            text_chunks_db,
            query_param,
            tokenizer,
        )
        hl_data = await _get_edge_data(
            hl_keywords,
            knowledge_graph_inst,
            relationships_vdb,
            text_chunks_db,
            query_param,
            tokenizer,
        )

        (
            ll_entities_context,
            ll_relations_context,
            ll_text_units_context,
        ) = ll_data

        (
            hl_entities_context,
            hl_relations_context,
            hl_text_units_context,
        ) = hl_data

        # Initialize vector data with empty lists
        vector_entities_context, vector_relations_context, vector_text_units_context = (
            [],
            [],
            [],
        )
        #
        # Only get vector data if in mix mode
        if query_param.mode == "mix" and hasattr(query_param, "original_query"):
            # Get vector context in triple format
            vector_data = await _get_vector_context(
                query_param.original_query,  # We need to pass the original query
                chunks_vdb,
                query_param,
                tokenizer,
            )  # 用原始问题，基于embedding相似度检索分段数据

            # If vector_data is not None, unpack it
            if vector_data is not None:
                (
                    vector_entities_context,
                    vector_relations_context,
                    vector_text_units_context,
                ) = vector_data
        # 对节点检索、边检索、分段检索数据进行去重合并
        # Combine and deduplicate the entities, relationships, and sources
        entities_context = process_combine_contexts(hl_entities_context, ll_entities_context, vector_entities_context)
        relations_context = process_combine_contexts(
            hl_relations_context, ll_relations_context, vector_relations_context
        )
        text_units_context = process_combine_contexts(
            hl_text_units_context, ll_text_units_context, vector_text_units_context
        )
    # not necessary to use LLM to generate a response
    if not entities_context and not relations_context:
        return None

    return entities_context, relations_context, text_units_context


async def _get_node_data(
    query: str,  # 低级别关键词【侧重于特定实体、细节或具体术语】
    knowledge_graph_inst: BaseGraphStorage,
    entities_vdb: BaseVectorStorage,
    text_chunks_db: BaseKVStorage,
    query_param: QueryParam,
    tokenizer: Tokenizer,
):
    # get similar entities
    logger.info(
        f"Query nodes: {query}, top_k: {query_param.top_k}, cosine: {entities_vdb.cosine_better_than_threshold}"
    )

    results = await entities_vdb.query(query, top_k=query_param.top_k, ids=query_param.ids)  # 基于embedding相似度机制检索节点数据【表：lightrag_vdb_entity】

    if not len(results):
        return "", "", ""

    # Extract all entity IDs from your results list
    node_ids = [r["entity_name"] for r in results]  # 提取embedding相似度检索结果中的节点id列表

    # Call the batch node retrieval and degree functions concurrently.
    nodes_dict, degrees_dict = await asyncio.gather(
        knowledge_graph_inst.get_nodes_batch(node_ids),  # 基于节点id列表查询节点数据【表：lightrag_graph_nodes】
        knowledge_graph_inst.node_degrees_batch(node_ids),  # 基于节点id列表查询相应节点的度【连接边的数量；解释：当前节点即可作为起点，也可作为终点】【表：lightrag_graph_edges】
    )  #

    # Now, if you need the node data and degree in order:
    node_datas = [nodes_dict.get(nid) for nid in node_ids]
    node_degrees = [degrees_dict.get(nid, 0) for nid in node_ids]

    if not all([n is not None for n in node_datas]):
        logger.warning("Some nodes are missing, maybe the storage is damaged")

    node_datas = [
        {
            **n,
            "entity_name": k["entity_name"],
            "rank": d,
            "created_at": k.get("created_at"),
        }
        for k, n, d in zip(results, node_datas, node_degrees)
        if n is not None
    ]  # what is this text_chunks_db doing.  dont remember it in airvx.  check the diagram.
    # get entitytext chunk
    use_text_units = await _find_most_related_text_unit_from_entities(
        node_datas,
        query_param,
        text_chunks_db,
        knowledge_graph_inst,
        tokenizer,
    )  # TODO 待分析~
    use_relations = await _find_most_related_edges_from_entities(
        node_datas,
        query_param,
        knowledge_graph_inst,
        tokenizer,
    )

    len_node_datas = len(node_datas)
    node_datas = truncate_list_by_token_size(
        node_datas,
        key=lambda x: x["description"] if x["description"] is not None else "",
        max_token_size=query_param.max_token_for_local_context,
        tokenizer=tokenizer,
    )
    logger.debug(
        f"Truncate entities from {len_node_datas} to {len(node_datas)} (max tokens:{query_param.max_token_for_local_context})"
    )

    logger.info(
        f"Local query uses {len(node_datas)} entites, {len(use_relations)} relations, {len(use_text_units)} chunks"
    )

    # build prompt
    entities_context = []
    for i, n in enumerate(node_datas):
        created_at = n.get("created_at", "UNKNOWN")
        if isinstance(created_at, (int, float)):
            created_at = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(created_at))

        # Get file path from node data
        file_path = n.get("file_path", "unknown_source")

        entities_context.append(
            {
                "id": i + 1,
                "entity": n["entity_name"],
                "type": n.get("entity_type", "UNKNOWN"),
                "description": n.get("description", "UNKNOWN"),
                "rank": n["rank"],
                "created_at": created_at,
                "file_path": file_path,
            }
        )

    relations_context = []
    for i, e in enumerate(use_relations):
        created_at = e.get("created_at", "UNKNOWN")
        # Convert timestamp to readable format
        if isinstance(created_at, (int, float)):
            created_at = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(created_at))

        # Get file path from edge data
        file_path = e.get("file_path", "unknown_source")

        relations_context.append(
            {
                "id": i + 1,
                "entity1": e["src_tgt"][0],
                "entity2": e["src_tgt"][1],
                "description": e["description"],
                "keywords": e["keywords"],
                "weight": e["weight"],
                "rank": e["rank"],
                "created_at": created_at,
                "file_path": file_path,
            }
        )

    text_units_context = []
    for i, t in enumerate(use_text_units):
        text_units_context.append(
            {
                "id": i + 1,
                "content": t["content"],
                "file_path": t.get("file_path", "unknown_source"),
            }
        )
    return entities_context, relations_context, text_units_context


async def _find_most_related_text_unit_from_entities(
    node_datas: list[dict],  # 节点数据列表【内含：节点名称、节点描述、节点来源分段id】
    query_param: QueryParam,  # 检索参数
    text_chunks_db: BaseKVStorage,  # 分段数据存储实例
    knowledge_graph_inst: BaseGraphStorage,  # 知识图谱数据存储实例
    tokenizer: Tokenizer,  # 分词器
):  # 寻找与实体列表最相关的文本块 TODO 至此~
    """
    这段代码的核心作用是：**从知识图谱的检索结果（节点数据）中，筛选、关联并排序出与查询最相关的文本块（text units）**，最终为后续的语义理解或回答生成提供高质量的文本素材。整体逻辑围绕“节点关联的文本块”和“节点间关系”展开，具体可拆解为5个关键步骤：


    ### **1. 提取初始节点关联的文本块ID**
    - **操作**：从输入的 `node_datas`（检索到的节点数据列表）中，提取每个节点的 `source_id` 字段，并用分隔符（`GRAPH_FIELD_SEP`）拆分得到“文本块ID列表”（`text_units`）。
    - **目的**：每个节点可能关联多个原始文本片段（如文档中的某段话），`source_id` 记录了这些文本块的唯一标识，这里先解析出这些ID，用于后续获取具体文本内容。


    ### **2. 收集节点的“一跳邻居”及关联文本**
    - **步骤拆解**：
      1. 从知识图谱中获取每个节点的直接关联边（`edges`），即“与该节点相连的其他节点”（一跳邻居）。
      2. 汇总所有一跳邻居节点，形成 `all_one_hop_nodes` 集合（去重）。
      3. 获取这些一跳邻居节点的详细数据（`all_one_hop_nodes_data`），并提取它们关联的文本块ID，存入 `all_one_hop_text_units_lookup`（键为邻居节点名，值为其关联的文本块ID集合）。
    - **目的**：不仅考虑初始节点本身的文本，还纳入其邻居节点的关联文本，扩大相关文本的覆盖范围（利用知识图谱的关联性补充信息）。


    ### **3. 批量获取文本块内容并建立关联映射**
    - **步骤拆解**：
      1. 整合初始节点和邻居节点的所有文本块ID，去重后存入 `all_text_units_lookup`（避免重复处理）。
      2. 按批次（`batch_size=5`）从文本存储（`text_chunks_db`）中获取这些文本块的具体内容（`data`），避免单次请求压力过大。
      3. 为每个文本块记录额外信息：
         - `order`：文本块所属初始节点在 `node_datas` 中的索引（保留原始检索的优先级）。
         - `relation_counts`：该文本块与初始节点的邻居节点的关联次数（关联越多，说明文本与图谱结构的相关性越强）。
    - **目的**：将文本块内容与知识图谱的节点关系绑定，为后续排序提供依据。


    ### **4. 筛选有效文本块并排序**
    - **筛选**：过滤掉内容为空或无效的文本块（确保 `data` 存在且包含 `content` 字段）。
    - **排序**：按两个维度对文本块排序：
      1. 优先按 `order` 升序（保留初始节点的检索优先级，先检索到的节点关联文本更优先）。
      2. 同 `order` 内按 `relation_counts` 降序（与邻居节点关联越多的文本块，权重越高）。
    - **目的**：让与查询关联最紧密、结构相关性最强的文本块排在前面。


    ### **5. 按token长度截断文本块列表**
    - **操作**：使用 `truncate_list_by_token_size` 函数，根据 `query_param.max_token_for_text_unit` 限制，按文本内容的token长度（通过 `tokenizer` 计算）截断列表，确保总长度不超过阈值。
    - **目的**：控制文本总量，避免后续处理（如大模型输入）因token超限而失败，同时保留最关键的文本。


    ### **总结：代码的核心价值**
    1. **关联知识图谱与文本**：将知识图谱的节点/边关系（结构信息）与原始文本块（内容信息）结合，避免仅依赖文本相似度的检索局限。
    2. **优化文本排序**：通过“初始检索优先级”和“节点关联强度”双重维度排序，提升文本块的相关性。
    3. **控制资源与格式**：批量处理+token截断，确保效率和兼容性。

    最终输出的 `all_text_units` 是经过筛选、排序、截断后的高质量文本块列表，可直接用于后续的语义理解或回答生成。
    """
    text_units = [
        split_string_by_multi_markers(dp["source_id"], [GRAPH_FIELD_SEP])
        for dp in node_datas
        if dp["source_id"] is not None
    ]  # 提取node_datas中的来源分段id列表

    node_names = [dp["entity_name"] for dp in node_datas]  # 提取node_datas中的所有节点名称
    batch_edges_dict = await knowledge_graph_inst.get_nodes_edges_batch(node_names)  # 提取node_datas中所有节点关联的边
    # Build the edges list in the same order as node_datas.
    edges = [batch_edges_dict.get(name, []) for name in node_names]  # 按照node_datas中节点名称的顺序，构造其关联的边列表【如果存在某节点没有边，则采用[]占位】

    all_one_hop_nodes = set()
    for this_edges in edges:
        if not this_edges:
            continue
        all_one_hop_nodes.update([e[1] for e in this_edges])  # TODO 由于在获取节点关联的边时，该节点既可作为边的起点，又可作为边的终点。这里直接取边的终点作为一跳节点存在问题吧？

    all_one_hop_nodes = list(all_one_hop_nodes)
    # 获取所有一跳节点的数据
    # Batch retrieve one-hop node data using get_nodes_batch
    all_one_hop_nodes_data_dict = await knowledge_graph_inst.get_nodes_batch(all_one_hop_nodes)
    all_one_hop_nodes_data = [all_one_hop_nodes_data_dict.get(e) for e in all_one_hop_nodes]

    # Add null check for node data
    all_one_hop_text_units_lookup = {
        k: set(split_string_by_multi_markers(v["source_id"], [GRAPH_FIELD_SEP]))
        for k, v in zip(all_one_hop_nodes, all_one_hop_nodes_data)
        if v is not None and "source_id" in v  # Add source_id check
    }  # 获取所有一跳节点的来源分段id列表

    all_text_units_lookup = {}
    tasks = []

    for index, (this_text_units, this_edges) in enumerate(zip(text_units, edges)):
        for c_id in this_text_units:
            if c_id not in all_text_units_lookup:
                all_text_units_lookup[c_id] = index
                tasks.append((c_id, index, this_edges))

    # Process in batches tasks at a time to avoid overwhelming resources
    batch_size = 5
    results = []

    for i in range(0, len(tasks), batch_size):
        batch_tasks = tasks[i : i + batch_size]
        batch_results = await asyncio.gather(*[text_chunks_db.get_by_id(c_id) for c_id, _, _ in batch_tasks])
        results.extend(batch_results)

    for (c_id, index, this_edges), data in zip(tasks, results):
        all_text_units_lookup[c_id] = {
            "data": data,
            "order": index,
            "relation_counts": 0,
        }

        if this_edges:
            for e in this_edges:
                if e[1] in all_one_hop_text_units_lookup and c_id in all_one_hop_text_units_lookup[e[1]]:
                    all_text_units_lookup[c_id]["relation_counts"] += 1

    # Filter out None values and ensure data has content
    all_text_units = [
        {"id": k, **v}
        for k, v in all_text_units_lookup.items()
        if v is not None and v.get("data") is not None and "content" in v["data"]
    ]

    if not all_text_units:
        logger.warning("No valid text units found")
        return []

    all_text_units = sorted(all_text_units, key=lambda x: (x["order"], -x["relation_counts"]))
    all_text_units = truncate_list_by_token_size(
        all_text_units,
        key=lambda x: x["data"]["content"],
        max_token_size=query_param.max_token_for_text_unit,
        tokenizer=tokenizer,
    )

    logger.debug(
        f"Truncate chunks from {len(all_text_units_lookup)} to {len(all_text_units)} (max tokens:{query_param.max_token_for_text_unit})"
    )

    all_text_units = [t["data"] for t in all_text_units]
    return all_text_units


async def _find_most_related_edges_from_entities(
    node_datas: list[dict],
    query_param: QueryParam,
    knowledge_graph_inst: BaseGraphStorage,
    tokenizer: Tokenizer,
):
    node_names = [dp["entity_name"] for dp in node_datas]
    batch_edges_dict = await knowledge_graph_inst.get_nodes_edges_batch(node_names)

    all_edges = []
    seen = set()

    for node_name in node_names:
        this_edges = batch_edges_dict.get(node_name, [])
        for e in this_edges:
            sorted_edge = tuple(sorted(e))
            if sorted_edge not in seen:
                seen.add(sorted_edge)
                all_edges.append(sorted_edge)

    # Prepare edge pairs in two forms:
    # For the batch edge properties function, use dicts.
    edge_pairs_dicts = [{"src": e[0], "tgt": e[1]} for e in all_edges]
    # For edge degrees, use tuples.
    edge_pairs_tuples = list(all_edges)  # all_edges is already a list of tuples

    # Call the batched functions concurrently.
    edge_data_dict, edge_degrees_dict = await asyncio.gather(
        knowledge_graph_inst.get_edges_batch(edge_pairs_dicts),
        knowledge_graph_inst.edge_degrees_batch(edge_pairs_tuples),
    )

    # Reconstruct edge_datas list in the same order as the deduplicated results.
    all_edges_data = []
    for pair in all_edges:
        edge_props = edge_data_dict.get(pair)
        if edge_props is not None:
            if "weight" not in edge_props:
                logger.warning(f"Edge {pair} missing 'weight' attribute, using default value 0.0")
                edge_props["weight"] = 0.0

            combined = {
                "src_tgt": pair,
                "rank": edge_degrees_dict.get(pair, 0),
                **edge_props,
            }
            all_edges_data.append(combined)

    all_edges_data = sorted(all_edges_data, key=lambda x: (x["rank"], x["weight"]), reverse=True)
    all_edges_data = truncate_list_by_token_size(
        all_edges_data,
        key=lambda x: x["description"] if x["description"] is not None else "",
        max_token_size=query_param.max_token_for_global_context,
        tokenizer=tokenizer,
    )

    logger.debug(
        f"Truncate relations from {len(all_edges)} to {len(all_edges_data)} (max tokens:{query_param.max_token_for_global_context})"
    )

    return all_edges_data


async def _get_edge_data(
    keywords,  # 高级关键字【侧重于总体概念或主题】
    knowledge_graph_inst: BaseGraphStorage,
    relationships_vdb: BaseVectorStorage,
    text_chunks_db: BaseKVStorage,
    query_param: QueryParam,
    tokenizer: Tokenizer,
):
    logger.info(
        f"Query edges: {keywords}, top_k: {query_param.top_k}, cosine: {relationships_vdb.cosine_better_than_threshold}"
    )

    results = await relationships_vdb.query(keywords, top_k=query_param.top_k, ids=query_param.ids)  # 基于embedding相似度机制检索边数据【表：lightrag_vdb_relation】

    if not len(results):
        return "", "", ""
    # 提取embedding相似度检索结果中的节点id列表
    # Prepare edge pairs in two forms:
    # For the batch edge properties function, use dicts.
    edge_pairs_dicts = [{"src": r["src_id"], "tgt": r["tgt_id"]} for r in results]
    # For edge degrees, use tuples.
    edge_pairs_tuples = [(r["src_id"], r["tgt_id"]) for r in results]

    # Call the batched functions concurrently.
    edge_data_dict, edge_degrees_dict = await asyncio.gather(
        knowledge_graph_inst.get_edges_batch(edge_pairs_dicts),  # 基于边起止节点id元组列表查询边数据【表：lightrag_graph_edges】
        knowledge_graph_inst.edge_degrees_batch(edge_pairs_tuples),  # 基于边起止节点id元组列表查询相应边的度【其源节点和目标节点的度数之和】【表：lightrag_graph_edges】
    )

    # Reconstruct edge_datas list in the same order as results.
    edge_datas = []
    for k in results:
        pair = (k["src_id"], k["tgt_id"])
        edge_props = edge_data_dict.get(pair)
        if edge_props is not None:
            if "weight" not in edge_props:
                logger.warning(f"Edge {pair} missing 'weight' attribute, using default value 0.0")
                edge_props["weight"] = 0.0

            # Use edge degree from the batch as rank.
            combined = {
                "src_id": k["src_id"],
                "tgt_id": k["tgt_id"],
                "rank": edge_degrees_dict.get(pair, k.get("rank", 0)),
                "created_at": k.get("created_at", None),
                **edge_props,
            }
            edge_datas.append(combined)

    edge_datas = sorted(edge_datas, key=lambda x: (x["rank"], x["weight"]), reverse=True)
    edge_datas = truncate_list_by_token_size(
        edge_datas,
        key=lambda x: x["description"] if x["description"] is not None else "",
        max_token_size=query_param.max_token_for_global_context,
        tokenizer=tokenizer,
    )
    use_entities, use_text_units = await asyncio.gather(
        _find_most_related_entities_from_relationships(
            edge_datas,
            query_param,
            knowledge_graph_inst,
            tokenizer,
        ),
        _find_related_text_unit_from_relationships(
            edge_datas,
            query_param,
            text_chunks_db,
            tokenizer,
        ),
    )
    logger.info(
        f"Global query uses {len(use_entities)} entites, {len(edge_datas)} relations, {len(use_text_units)} chunks"
    )

    relations_context = []
    for i, e in enumerate(edge_datas):
        created_at = e.get("created_at", "UNKNOWN")
        # Convert timestamp to readable format
        if isinstance(created_at, (int, float)):
            created_at = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(created_at))

        # Get file path from edge data
        file_path = e.get("file_path", "unknown_source")

        relations_context.append(
            {
                "id": i + 1,
                "entity1": e["src_id"],
                "entity2": e["tgt_id"],
                "description": e["description"],
                "keywords": e["keywords"],
                "weight": e["weight"],
                "rank": e["rank"],
                "created_at": created_at,
                "file_path": file_path,
            }
        )

    entities_context = []
    for i, n in enumerate(use_entities):
        created_at = n.get("created_at", "UNKNOWN")
        # Convert timestamp to readable format
        if isinstance(created_at, (int, float)):
            created_at = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(created_at))

        # Get file path from node data
        file_path = n.get("file_path", "unknown_source")

        entities_context.append(
            {
                "id": i + 1,
                "entity": n["entity_name"],
                "type": n.get("entity_type", "UNKNOWN"),
                "description": n.get("description", "UNKNOWN"),
                "rank": n["rank"],
                "created_at": created_at,
                "file_path": file_path,
            }
        )

    text_units_context = []
    for i, t in enumerate(use_text_units):
        text_units_context.append(
            {
                "id": i + 1,
                "content": t["content"],
                "file_path": t.get("file_path", "unknown"),
            }
        )
    return entities_context, relations_context, text_units_context


async def _find_most_related_entities_from_relationships(
    edge_datas: list[dict],
    query_param: QueryParam,
    knowledge_graph_inst: BaseGraphStorage,
    tokenizer: Tokenizer,
):
    entity_names = []
    seen = set()

    for e in edge_datas:
        if e["src_id"] not in seen:
            entity_names.append(e["src_id"])
            seen.add(e["src_id"])
        if e["tgt_id"] not in seen:
            entity_names.append(e["tgt_id"])
            seen.add(e["tgt_id"])

    # Batch approach: Retrieve nodes and their degrees concurrently with one query each.
    nodes_dict, degrees_dict = await asyncio.gather(
        knowledge_graph_inst.get_nodes_batch(entity_names),
        knowledge_graph_inst.node_degrees_batch(entity_names),
    )

    # Rebuild the list in the same order as entity_names
    node_datas = []
    for entity_name in entity_names:
        node = nodes_dict.get(entity_name)
        degree = degrees_dict.get(entity_name, 0)
        if node is None:
            logger.warning(f"Node '{entity_name}' not found in batch retrieval.")
            continue
        # Combine the node data with the entity name and computed degree (as rank)
        combined = {**node, "entity_name": entity_name, "rank": degree}
        node_datas.append(combined)

    len_node_datas = len(node_datas)
    node_datas = truncate_list_by_token_size(
        node_datas,
        key=lambda x: x["description"] if x["description"] is not None else "",
        max_token_size=query_param.max_token_for_local_context,
        tokenizer=tokenizer,
    )
    logger.debug(
        f"Truncate entities from {len_node_datas} to {len(node_datas)} (max tokens:{query_param.max_token_for_local_context})"
    )

    return node_datas


async def _find_related_text_unit_from_relationships(
    edge_datas: list[dict],
    query_param: QueryParam,
    text_chunks_db: BaseKVStorage,
    tokenizer: Tokenizer,
):
    text_units = [
        split_string_by_multi_markers(dp["source_id"], [GRAPH_FIELD_SEP])
        for dp in edge_datas
        if dp["source_id"] is not None
    ]
    all_text_units_lookup = {}

    async def fetch_chunk_data(c_id, index):
        if c_id not in all_text_units_lookup:
            chunk_data = await text_chunks_db.get_by_id(c_id)
            # Only store valid data
            if chunk_data is not None and "content" in chunk_data:
                all_text_units_lookup[c_id] = {
                    "data": chunk_data,
                    "order": index,
                }

    tasks = []
    for index, unit_list in enumerate(text_units):
        for c_id in unit_list:
            tasks.append(fetch_chunk_data(c_id, index))

    await asyncio.gather(*tasks)

    if not all_text_units_lookup:
        logger.warning("No valid text chunks found")
        return []

    all_text_units = [{"id": k, **v} for k, v in all_text_units_lookup.items()]
    all_text_units = sorted(all_text_units, key=lambda x: x["order"])

    # Ensure all text chunks have content
    valid_text_units = [t for t in all_text_units if t["data"] is not None and "content" in t["data"]]

    if not valid_text_units:
        logger.warning("No valid text chunks after filtering")
        return []

    truncated_text_units = truncate_list_by_token_size(
        valid_text_units,
        key=lambda x: x["data"]["content"],
        max_token_size=query_param.max_token_for_text_unit,
        tokenizer=tokenizer,
    )

    logger.debug(
        f"Truncate chunks from {len(valid_text_units)} to {len(truncated_text_units)} (max tokens:{query_param.max_token_for_text_unit})"
    )

    all_text_units: list[TextChunkSchema] = [t["data"] for t in truncated_text_units]

    return all_text_units


async def naive_query(
    query: str,
    chunks_vdb: BaseVectorStorage,
    query_param: QueryParam,
    llm_model_func,
    tokenizer,
    system_prompt: str | None = None,
) -> str | AsyncIterator[str]:
    if query_param.model_func:
        use_model_func = query_param.model_func
    else:
        use_model_func = llm_model_func

    _, _, text_units_context = await _get_vector_context(query, chunks_vdb, query_param, tokenizer)

    if text_units_context is None or len(text_units_context) == 0:
        return PROMPTS["fail_response"]

    text_units_str = json.dumps(text_units_context, ensure_ascii=False)
    if query_param.only_need_context:
        return f"""
---Document Chunks---

```json
{text_units_str}
```

"""
    # Process conversation history
    history_context = ""
    if query_param.conversation_history:
        history_context = get_conversation_turns(query_param.conversation_history, query_param.history_turns)

    # Build system prompt
    user_prompt = query_param.user_prompt if query_param.user_prompt else PROMPTS["DEFAULT_USER_PROMPT"]
    sys_prompt_temp = system_prompt if system_prompt else PROMPTS["naive_rag_response"]
    sys_prompt = sys_prompt_temp.format(
        content_data=text_units_str,
        response_type=query_param.response_type,
        history=history_context,
        user_prompt=user_prompt,
    )

    if query_param.only_need_prompt:
        return sys_prompt

    len_of_prompts = len(tokenizer.encode(query + sys_prompt))
    logger.debug(f"[naive_query]Prompt Tokens: {len_of_prompts}")

    response = await use_model_func(
        query,
        system_prompt=sys_prompt,
        stream=query_param.stream,
    )

    if isinstance(response, str) and len(response) > len(sys_prompt):
        response = (
            response[len(sys_prompt) :]
            .replace(sys_prompt, "")
            .replace("user", "")
            .replace("model", "")
            .replace(query, "")
            .replace("<system>", "")
            .replace("</system>", "")
            .strip()
        )

    return response


# ============= Merge Suggestions Functions =============


async def get_high_degree_nodes(
    graph_storage: BaseGraphStorage,
    max_analyze_nodes: int = 500,
    batch_size: int = 100,
    lightrag_logger=None,
) -> tuple[GraphNodeDataDict, int]:
    """
    Get high-degree nodes from the graph prioritized by connectivity.

    Args:
        graph_storage: Graph storage instance
        max_analyze_nodes: Maximum number of nodes to analyze (default: 500)
        batch_size: Batch size for processing (default: 100)
        lightrag_logger: Logger instance

    Returns:
        Tuple of (selected_nodes_dict, total_nodes_analyzed)

    Example:
        Input: Graph with 1000 nodes, max_analyze_nodes=300
        Output: (GraphNodeDataDict with 300 nodes, 1000)
    """
    # Get all node labels
    all_labels = await graph_storage.get_all_labels()
    if not all_labels:
        return GraphNodeDataDict(nodes_by_id={}), 0

    if lightrag_logger:
        lightrag_logger.debug(f"Found {len(all_labels)} total nodes in graph")

    # Process nodes in batches to get degrees
    high_degree_nodes = []
    all_degrees = {}

    for i in range(0, len(all_labels), batch_size):
        batch_labels = all_labels[i : i + batch_size]
        batch_degrees = await graph_storage.node_degrees_batch(batch_labels)

        # Collect all degrees for return
        all_degrees.update(batch_degrees)

        # Collect nodes with their degrees
        for label in batch_labels:
            degree = batch_degrees.get(label, 0)
            if degree > 0:  # Only consider connected nodes
                high_degree_nodes.append((label, degree))

    # Sort by degree and take top nodes
    high_degree_nodes.sort(key=lambda x: x[1], reverse=True)
    selected_labels = [label for label, _ in high_degree_nodes[:max_analyze_nodes]]

    # Get detailed node data for selected nodes (avoid redundant query in filter_and_group_entities)
    nodes_data_raw = {}
    if selected_labels:
        nodes_data_raw = await graph_storage.get_nodes_batch(selected_labels)

    # Convert raw dict data to GraphNodeData objects with degree information
    nodes_by_id = {}
    for label, raw_data in nodes_data_raw.items():
        # Ensure entity_id is set
        if "entity_id" not in raw_data:
            raw_data["entity_id"] = label

        # Add degree information to the node data
        raw_data["degree"] = all_degrees.get(label, 0)

        nodes_by_id[label] = GraphNodeData(**raw_data)

    if lightrag_logger:
        lightrag_logger.debug(f"Selected {len(selected_labels)} high-degree nodes and retrieved their data")

    return GraphNodeDataDict(nodes_by_id=nodes_by_id), len(all_labels)


async def filter_and_group_entities(
    selected_nodes_dict: GraphNodeDataDict,
    entity_types: list[str] | None = None,
) -> dict[str, list[GraphNodeData]]:
    """
    Filter nodes by entity types and group them by type.

    Args:
        selected_nodes_dict: Dictionary of selected nodes with their data
        entity_types: Optional filter for specific entity types

    Returns:
        Dictionary mapping entity types to lists of GraphNodeData objects

    Example:
        Input: selected_nodes_dict=GraphNodeDataDict(...), entity_types=['PERSON']
        Output: {'PERSON': [GraphNodeData(entity_id='entity1', ...)]}
    """
    # Filter by entity types if specified
    filtered_nodes = {}
    for label, node_data in selected_nodes_dict.nodes_by_id.items():
        if entity_types:
            entity_type = node_data.entity_type or ""
            if entity_type not in entity_types:
                continue
        filtered_nodes[label] = node_data

    if not filtered_nodes:
        return {}

    # Group entities by type
    from collections import defaultdict

    entities_by_type = defaultdict(list)
    for label, node_data in filtered_nodes.items():
        entity_type = node_data.entity_type or "UNKNOWN"
        filtered_node_data = GraphNodeData(
            entity_id=label,
            entity_name=node_data.entity_name or label,
            entity_type=entity_type,
            description=node_data.description or "",
            degree=node_data.degree,
            source_id=node_data.source_id,
            file_path=node_data.file_path,
            created_at=node_data.created_at,
        )
        entities_by_type[entity_type].append(filtered_node_data)

    return dict(entities_by_type)


async def analyze_entities_with_llm(
    entities_by_type: dict[str, list[GraphNodeData]],
    llm_model_func: callable,
    confidence_threshold: float = 0.6,
    batch_size: int = 50,
    max_suggestions: int = 10,  # Add max_suggestions parameter for early exit
    max_concurrent_llm_calls: int = 4,  # Add concurrent LLM calls limit
    tokenizer=None,
    llm_model_max_token_size: int = 32768,
    summary_to_max_tokens: int = 200,
    lightrag_logger=None,
) -> list[MergeSuggestion]:
    """
    Analyze entities using LLM to identify merge candidates with concurrent processing and early exit optimization.

    Args:
        entities_by_type: Dictionary mapping entity types to GraphNodeData lists
        llm_model_func: LLM function for analysis
        confidence_threshold: Minimum confidence score to accept suggestions (default: 0.6)
        batch_size: Batch size for LLM processing (default: 50)
        max_suggestions: Maximum suggestions to return - enables early exit (default: 10)
        max_concurrent_llm_calls: Maximum concurrent LLM calls (default: 4)
        tokenizer: Tokenizer for description handling
        llm_model_max_token_size: Max token size for LLM
        summary_to_max_tokens: Max tokens for summaries
        lightrag_logger: Logger instance

    Returns:
        List of MergeSuggestion objects (up to max_suggestions)

    Example:
        Input: entities_by_type={'PERSON': [GraphNodeData('Alice Smith'), GraphNodeData('A. Smith')]}
        Output: [MergeSuggestion(entities=[...], confidence_score=0.85, ...)]
    """
    suggestions = []

    if not llm_model_func:
        if lightrag_logger:
            lightrag_logger.warning("No LLM function provided, skipping LLM analysis")
        return suggestions

    # Track processed entities for debugging
    total_entities_processed = 0
    total_batches_prepared = 0

    # For early exit tracking
    seen_entities = set()

    # Prepare all batches for concurrent processing
    batch_tasks_data = []

    # Process each entity type and create batch task data
    for entity_type, entities_list in entities_by_type.items():
        if len(entities_list) < 2:
            if lightrag_logger:
                lightrag_logger.debug(f"Skipping {entity_type}: only {len(entities_list)} entities")
            continue  # Skip types with only one entity

        if lightrag_logger:
            lightrag_logger.debug(f"Preparing {entity_type}: {len(entities_list)} entities in batches of {batch_size}")

        # Create batch tasks for this entity type
        for i in range(0, len(entities_list), batch_size):
            batch_entities = entities_list[i : i + batch_size]
            total_batches_prepared += 1
            total_entities_processed += len(batch_entities)

            batch_tasks_data.append(
                {
                    "batch_id": total_batches_prepared,
                    "entity_type": entity_type,
                    "entities": batch_entities,
                    "batch_size": len(batch_entities),
                }
            )

    if not batch_tasks_data:
        if lightrag_logger:
            lightrag_logger.info("No valid batches to process")
        return suggestions

    if lightrag_logger:
        lightrag_logger.info(
            f"Starting concurrent LLM analysis: {total_batches_prepared} batches, "
            f"{total_entities_processed} entities, max_concurrent={max_concurrent_llm_calls}"
        )

    # Create semaphore for controlling concurrency and lock for protecting shared state
    semaphore = asyncio.Semaphore(max_concurrent_llm_calls)
    shared_state_lock = asyncio.Lock()  # Lock to protect shared variables
    successful_batches = 0
    processed_batches = 0

    async def _process_batch_with_semaphore(batch_data):
        """Process a single batch with semaphore control"""
        nonlocal suggestions, seen_entities, successful_batches, processed_batches

        async with semaphore:
            batch_id = batch_data["batch_id"]
            entity_type = batch_data["entity_type"]
            batch_entities = batch_data["entities"]

            if lightrag_logger:
                lightrag_logger.debug(f"Processing batch {batch_id} for {entity_type}: {len(batch_entities)} entities")

            try:
                batch_suggestions = await _batch_analyze_entities_with_llm(
                    batch_entities,
                    llm_model_func,
                    confidence_threshold,
                    tokenizer,
                    llm_model_max_token_size,
                    summary_to_max_tokens,
                    lightrag_logger,
                )

                # Protect shared state modifications with lock
                async with shared_state_lock:
                    processed_batches += 1

                    if batch_suggestions:
                        # Apply immediate filtering and deduplication
                        filtered_batch_suggestions = []
                        for suggestion in batch_suggestions:
                            entity_ids = {entity.entity_id for entity in suggestion.entities}
                            # Check for overlap with already seen entities
                            if not (entity_ids & seen_entities):
                                filtered_batch_suggestions.append(suggestion)
                                seen_entities.update(entity_ids)

                        successful_batches += 1

                        if lightrag_logger:
                            lightrag_logger.debug(
                                f"Batch {batch_id} produced {len(batch_suggestions)} raw suggestions, "
                                f"{len(filtered_batch_suggestions)} after filtering"
                            )

                        return filtered_batch_suggestions
                    else:
                        if lightrag_logger:
                            lightrag_logger.debug(f"Batch {batch_id} produced no suggestions")
                        return []

            except Exception as e:
                # Protect shared state modifications with lock
                async with shared_state_lock:
                    processed_batches += 1
                if lightrag_logger:
                    lightrag_logger.warning(f"Batch LLM analysis failed for {entity_type} batch {batch_id}: {e}")
                return []

    # Create tasks for all batches
    tasks = []
    for batch_data in batch_tasks_data:
        task = asyncio.create_task(_process_batch_with_semaphore(batch_data))
        tasks.append(task)

    # Wait for tasks to complete or for the first exception
    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)

    # Check if any task raised an exception
    for task in done:
        if task.exception():
            # Cancel all pending tasks
            for pending_task in pending:
                pending_task.cancel()

            # Wait for cancellation to complete
            if pending:
                await asyncio.wait(pending)

            # Re-raise the exception
            raise task.exception()

    # Collect results from all completed tasks
    for task in done:
        task_suggestions = task.result()
        if task_suggestions:
            suggestions.extend(task_suggestions)
            # Early exit check
            if len(suggestions) >= max_suggestions:
                if lightrag_logger:
                    lightrag_logger.info(
                        f"Early exit: reached max_suggestions ({max_suggestions}) during concurrent processing"
                    )
                # Cancel remaining tasks if we have enough suggestions
                for pending_task in pending:
                    pending_task.cancel()
                if pending:
                    await asyncio.wait(pending)
                break

    # Wait for any remaining tasks if we haven't hit the limit
    if len(suggestions) < max_suggestions and pending:
        remaining_done, _ = await asyncio.wait(pending)
        for task in remaining_done:
            if not task.cancelled():
                task_suggestions = task.result()
                if task_suggestions:
                    suggestions.extend(task_suggestions)
                    # Early exit check
                    if len(suggestions) >= max_suggestions:
                        break

    # Sort by confidence before returning (only sort what we have)
    suggestions.sort(key=lambda x: x.confidence_score, reverse=True)

    # Trim to max_suggestions if needed
    if len(suggestions) > max_suggestions:
        suggestions = suggestions[:max_suggestions]

    # Final logging with comprehensive stats
    if lightrag_logger:
        lightrag_logger.info(
            f"Concurrent LLM analysis completed: {len(suggestions)} suggestions found. "
            f"Processed {processed_batches}/{total_batches_prepared} batches concurrently "
            f"({successful_batches} successful). Confidence threshold: {confidence_threshold}, "
            f"Max concurrent: {max_concurrent_llm_calls}"
        )

        if suggestions:
            confidence_scores = [s.confidence_score for s in suggestions]
            lightrag_logger.debug(
                f"Suggestion confidence range: {min(confidence_scores):.2f} - {max(confidence_scores):.2f}"
            )
        else:
            lightrag_logger.warning(
                f"No suggestions found! This may indicate: "
                f"1) Confidence threshold ({confidence_threshold}) too high, "
                f"2) LLM parsing issues, or "
                f"3) No actual merge candidates exist"
            )

    return suggestions


async def _batch_analyze_entities_with_llm(
    entities_list: list[GraphNodeData],
    llm_model_func: callable,
    confidence_threshold: float,
    tokenizer,
    llm_model_max_token_size: int,
    summary_to_max_tokens: int,
    lightrag_logger,
) -> list[MergeSuggestion]:
    """
    Analyze a batch of entities using LLM to identify merge candidates.

    Args:
        entities_list: List of GraphNodeData objects to analyze
        llm_model_func: LLM function for analysis
        confidence_threshold: Minimum confidence score for suggestions
        tokenizer: Tokenizer for handling description length
        llm_model_max_token_size: Max token size for LLM
        summary_to_max_tokens: Max tokens for description summaries
        lightrag_logger: Logger instance

    Returns:
        List of MergeSuggestion objects

    Example:
        Input: entities_list=[GraphNodeData('Apple Inc'), GraphNodeData('Apple Company')]
        Output: [MergeSuggestion(confidence_score=0.9, merge_reason='Same organization')]
    """
    try:
        # Prepare entities list for prompt with description handling
        entities_text = ""
        for i, entity in enumerate(entities_list):
            # Skip description summarization to save LLM calls and time
            # Previously we would summarize long descriptions using _handle_entity_relation_summary
            # Now we use the original description as-is
            description = entity.description or ""

            entities_text += f"Entity {i + 1}:\n"
            entities_text += f"- Name: {entity.entity_name or entity.entity_id}\n"
            entities_text += f"- Type: {entity.entity_type or 'UNKNOWN'}\n"
            entities_text += f"- Description: {description}\n"
            entities_text += f"- Degree: {entity.degree or 0}\n\n"

        # Use prompt from prompts.py
        from .prompt import PROMPTS

        prompt = PROMPTS["batch_merge_analysis"].format(
            entities_list=entities_text,
            tuple_delimiter=PROMPTS["DEFAULT_TUPLE_DELIMITER"],
            record_delimiter=PROMPTS["DEFAULT_RECORD_DELIMITER"],
            completion_delimiter=PROMPTS["DEFAULT_COMPLETION_DELIMITER"],
            graph_field_sep=GRAPH_FIELD_SEP,
        )

        if lightrag_logger:
            lightrag_logger.debug(f"Sending {len(entities_list)} entities to LLM for merge analysis")

        # Call LLM
        response = await llm_model_func(
            prompt,
            system_prompt="You are a knowledge graph expert specialized in identifying entities that should be merged. Analyze the provided entities and identify groups that refer to the same real-world objects.",
            stream=False,
            temperature=0.1,
        )

        if lightrag_logger:
            lightrag_logger.debug(f"Received LLM response of length {len(response)} characters")

        # Parse LLM response
        suggestions = parse_llm_merge_response(response, entities_list, confidence_threshold, lightrag_logger)
        return suggestions

    except Exception as e:
        if lightrag_logger:
            lightrag_logger.warning(f"Batch LLM analysis failed: {e}")
        return []


def parse_llm_merge_response(
    llm_response: str, entities_list: list[GraphNodeData], confidence_threshold: float, lightrag_logger
) -> list[MergeSuggestion]:
    """
    Parse LLM response to extract merge suggestions.

    Args:
        llm_response: Raw LLM response text
        entities_list: Original list of GraphNodeData entities analyzed
        confidence_threshold: Minimum confidence score for suggestions
        lightrag_logger: Logger instance

    Returns:
        List of MergeSuggestion objects

    Example:
        Input: llm_response='("merge_group"<|>Apple Inc,Apple Company<|>0.9<|>Same organization<|>...)'
        Output: [MergeSuggestion(entities=[...], confidence_score=0.9, ...)]
    """
    suggestions = []

    try:
        # Create entity lookup for quick access
        entity_lookup = {(entity.entity_name or entity.entity_id): entity for entity in entities_list}

        # Split by record delimiter
        from .prompt import PROMPTS

        records = llm_response.split(PROMPTS["DEFAULT_RECORD_DELIMITER"])

        if lightrag_logger:
            lightrag_logger.debug(f"Parsing LLM response: found {len(records)} potential records")

        parsed_count = 0
        filtered_count = 0

        for i, record in enumerate(records):
            record = record.strip()
            if not record or PROMPTS["DEFAULT_COMPLETION_DELIMITER"] in record:
                continue

            suggestion = parse_single_merge_record(record, entity_lookup, confidence_threshold, lightrag_logger)
            if suggestion:
                suggestions.append(suggestion)
                parsed_count += 1
            else:
                filtered_count += 1

        if lightrag_logger:
            lightrag_logger.debug(
                f"Parsed {parsed_count} valid suggestions, filtered out {filtered_count} invalid/low-confidence records"
            )

    except Exception as e:
        if lightrag_logger:
            lightrag_logger.warning(f"Failed to parse merge suggestions: {e}")

    return suggestions


def parse_single_merge_record(
    record: str, entity_lookup: dict[str, GraphNodeData], confidence_threshold: float, lightrag_logger=None
) -> MergeSuggestion | None:
    """
    Parse a single merge record from LLM response.

    Expected format:
    ("merge_group"<|>Entity A<SEP>Entity B<|>0.85<|>reason<|>target_name<|>target_type)

    Args:
        record: Raw record string from LLM
        entity_lookup: Dict mapping entity names to GraphNodeData
        confidence_threshold: Minimum confidence score to accept
        lightrag_logger: Logger for debugging

    Returns:
        MergeSuggestion if successfully parsed and meets threshold, None otherwise
    """
    try:
        # Import required constants and types
        from .prompt import GRAPH_FIELD_SEP, PROMPTS
        from .types import GraphNodeData

        # Extract content between quotes and parentheses
        content = record.split('("merge_group"')[1].strip()
        if content.endswith(")"):
            content = content[:-1]

        # Parse the content using tuple delimiter
        parts = content.split(PROMPTS["DEFAULT_TUPLE_DELIMITER"])

        # Filter out empty parts (especially the first one if content starts with delimiter)
        parts = [part.strip() for part in parts if part.strip()]

        if len(parts) != 5:  # Now expecting 5 parts instead of 6
            if lightrag_logger:
                lightrag_logger.warning(f"Record has {len(parts)} parts, expected 5. Parts: {parts}")
                lightrag_logger.debug(f"Raw record: {record[:200]}...")
            return None

        # Extract entity names from GRAPH_FIELD_SEP-separated list
        entity_names_str = parts[0].strip()
        entity_names = []
        seen_names = set()  # Prevent duplicate entity names in the same suggestion

        for name in entity_names_str.split(GRAPH_FIELD_SEP):
            name = name.strip()
            if name and name in entity_lookup:
                # Only add if we haven't seen this entity name before
                if name not in seen_names:
                    entity_names.append(name)
                    seen_names.add(name)
                elif lightrag_logger:
                    lightrag_logger.debug(f"Skipping duplicate entity name '{name}' in merge suggestion")
            elif name and lightrag_logger:
                lightrag_logger.debug(f"Entity '{name}' not found in lookup")

        if len(entity_names) < 2:
            if lightrag_logger:
                lightrag_logger.debug(f"Not enough unique valid entities found: {entity_names}")
            return None

        # Parse confidence score
        try:
            confidence_score = float(parts[1].strip())
        except ValueError:
            if lightrag_logger:
                lightrag_logger.warning(f"Invalid confidence score: {parts[1]}")
            return None

        # Check confidence threshold
        if confidence_score < confidence_threshold:
            if lightrag_logger:
                lightrag_logger.debug(f"Confidence {confidence_score} below threshold {confidence_threshold}")
            return None

        # Extract other fields (no longer processing description)
        merge_reason = parts[2].strip()
        suggested_name = parts[3].strip()
        suggested_type = parts[4].strip()

        # Build entities list
        entities = [entity_lookup[name] for name in entity_names]

        if lightrag_logger:
            lightrag_logger.debug(
                f"Successfully parsed suggestion: {entity_names} -> {suggested_name} (confidence: {confidence_score})"
            )

        # Create suggested target entity as GraphNodeData object (without description)
        suggested_target_entity = GraphNodeData(
            entity_id=suggested_name,  # Use suggested name as entity_id
            entity_name=suggested_name,
            entity_type=suggested_type,
        )

        return MergeSuggestion(
            entities=entities,
            confidence_score=confidence_score,
            merge_reason=merge_reason,
            suggested_target_entity=suggested_target_entity,
        )

    except Exception as e:
        if lightrag_logger:
            lightrag_logger.warning(f"Failed to parse merge record: {e}")
            lightrag_logger.debug(f"Record content: {record}")
        return None


def filter_and_deduplicate_suggestions(
    suggestions: list[MergeSuggestion], max_suggestions: int
) -> list[MergeSuggestion]:
    """
    Filter and deduplicate merge suggestions.

    Args:
        suggestions: List of MergeSuggestion objects
        max_suggestions: Maximum number of suggestions to return

    Returns:
        Filtered and deduplicated list of suggestions
    """
    # Handle edge case where max_suggestions is 0
    if max_suggestions <= 0:
        return []

    # Sort by confidence score (highest first)
    suggestions.sort(key=lambda x: x.confidence_score, reverse=True)

    # Remove duplicates (same entity appearing in multiple suggestions)
    seen_entities = set()
    filtered_suggestions = []

    for suggestion in suggestions:
        entity_ids = {entity.entity_id for entity in suggestion.entities}
        if not (entity_ids & seen_entities):  # No overlap with seen entities
            filtered_suggestions.append(suggestion)
            seen_entities.update(entity_ids)
            if len(filtered_suggestions) >= max_suggestions:
                break

    return filtered_suggestions


def calculate_edit_distance(s1: str, s2: str) -> int:
    """
    Calculate Levenshtein distance between two strings.

    Args:
        s1: First string
        s2: Second string

    Returns:
        Edit distance as integer
    """
    if len(s1) < len(s2):
        s1, s2 = s2, s1

    if len(s2) == 0:
        return len(s1)

    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]
