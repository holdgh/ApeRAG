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
from dataclasses import dataclass, field
from functools import partial
from typing import (
    Any,
    AsyncIterator,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    final,
)

from aperag.graph.lightrag.constants import (
    DEFAULT_FORCE_LLM_SUMMARY_ON_MERGE,
    DEFAULT_MAX_TOKEN_SUMMARY,
)
from aperag.graph.lightrag.kg import (
    STORAGES,
    verify_storage_implementation,
)
from aperag.graph.lightrag.utils import LightRAGLogger, get_env_value

from .base import (
    BaseGraphStorage,
    BaseKVStorage,
    BaseVectorStorage,
    QueryParam,
    StoragesStatus,
)
from .namespace import NameSpace
from .operate import (
    build_query_context,
    chunking_by_token_size,
    extract_entities,
    kg_query,
    merge_nodes_and_edges,
    naive_query,
)
from .prompt import GRAPH_FIELD_SEP, PROMPTS
from .types import KnowledgeGraph
from .utils import (
    EmbeddingFunc,
    TiktokenTokenizer,
    Tokenizer,
    clean_text,
    compute_mdhash_id,
    create_lightrag_logger,
    logger,
)


@final
@dataclass
class LightRAG:
    """LightRAG: Simple and Fast Retrieval-Augmented Generation."""

    # Storage
    # ---

    kv_storage: str = field(default="PGOpsSyncKVStorage")
    """Storage backend for key-value data."""

    vector_storage: str = field(default="PGOpsSyncVectorStorage")
    """Storage backend for vector embeddings."""

    graph_storage: str = field(default="Neo4JSyncStorage")
    """Storage backend for knowledge graphs."""

    # Entity extraction
    # ---

    entity_extract_max_gleaning: int = field(default=1)  # 对不明确的内容尝试提取实体的最大次数【当前lightrag中默认0次】
    """Maximum number of entity extraction attempts for ambiguous content."""

    summary_to_max_tokens: int = field(default=get_env_value("MAX_TOKEN_SUMMARY", DEFAULT_MAX_TOKEN_SUMMARY, int))

    force_llm_summary_on_merge: int = field(
        default=get_env_value("FORCE_LLM_SUMMARY_ON_MERGE", DEFAULT_FORCE_LLM_SUMMARY_ON_MERGE, int)
    )

    # Text chunking
    # ---

    chunk_token_size: int = field(default=1200)
    """Maximum number of tokens per text chunk when splitting documents."""

    chunk_overlap_token_size: int = field(default=100)
    """Number of overlapping tokens between consecutive text chunks to preserve context."""

    tokenizer: Optional[Tokenizer] = field(default=None)  # 分词器实例，默认TiktokenTokenizer
    """
    A function that returns a Tokenizer instance.
    If None, and a `tiktoken_model_name` is provided, a TiktokenTokenizer will be created.
    If both are None, the default TiktokenTokenizer is used.
    """

    tiktoken_model_name: str = field(default="gpt-4o-mini")
    """Model name used for tokenization when chunking text with tiktoken. Defaults to `gpt-4o-mini`."""

    chunking_func: Callable[
        [
            Tokenizer,
            str,
            Optional[str],
            bool,
            int,
            int,
        ],
        List[Dict[str, Any]],
    ] = field(default_factory=lambda: chunking_by_token_size)  # 分段操作，默认为chunking_by_token_size
    """
    Custom chunking function for splitting text into chunks before processing.

    The function should take the following parameters:

        - `tokenizer`: A Tokenizer instance to use for tokenization.
        - `content`: The text to be split into chunks.
        - `split_by_character`: The character to split the text on. If None, the text is split into chunks of `chunk_token_size` tokens.
        - `split_by_character_only`: If True, the text is split only on the specified character.
        - `chunk_token_size`: The maximum number of tokens per chunk.
        - `chunk_overlap_token_size`: The number of overlapping tokens between consecutive chunks.

    The function should return a list of dictionaries, where each dictionary contains the following keys:
        - `tokens`: The number of tokens in the chunk.
        - `content`: The text content of the chunk.

    Defaults to `chunking_by_token_size` if not specified.
    """

    # Embedding
    # ---

    embedding_func: EmbeddingFunc | None = field(default=None)
    """Function for computing text embeddings. Must be set before use."""

    embedding_batch_num: int = field(default=32)
    """Batch size for embedding computations."""

    embedding_func_max_async: int = field(default=16)
    """Maximum number of concurrent embedding function calls."""

    embedding_cache_config: dict[str, Any] = field(
        default_factory=lambda: {
            "enabled": False,
            "similarity_threshold": 0.95,
            "use_llm_check": False,
        }
    )
    """Configuration for embedding cache.
    - enabled: If True, enables caching to avoid redundant computations.
    - similarity_threshold: Minimum similarity score to use cached embeddings.
    - use_llm_check: If True, validates cached embeddings using an LLM.
    """

    cosine_better_than_threshold: float = field(default=0.2)
    """
    Threshold for cosine similarity to determine if two embeddings are similar enough to be considered the same.
    """

    max_batch_size: int = field(default=32)
    """
    Maximum batch size for embedding computations.
    """

    # LLM Configuration
    # ---

    llm_model_func: Callable[..., object] | None = field(default=None)
    """Function for interacting with the large language model (LLM). Must be set before use."""

    llm_model_name: str = field(default="gpt-4o-mini")
    """Name of the LLM model used for generating responses."""

    llm_model_max_token_size: int = field(default=32768)
    """Maximum number of tokens allowed per LLM response."""

    llm_model_max_async: int = field(default=8)  # llm操作最大并发调用数
    """Maximum number of concurrent LLM calls."""

    llm_model_kwargs: dict[str, Any] = field(default_factory=dict)
    """Additional keyword arguments passed to the LLM model function."""

    # Storage
    # ---

    vector_db_storage_cls_kwargs: dict[str, Any] = field(default_factory=dict)
    """Additional parameters for vector database storage."""

    workspace: str = field(default="default")
    """Workspace identifier for data isolation across different collections/tenants."""

    # Extensions
    # ---
    # TODO 在lightrag实例的addon_params属性中可以自定义：实体类型【根据业务定义】、实体关系提取示例数量【默认全量，3个】。见aperag.graph.lightrag.operate.extract_entities中对于addon_params的使用
    addon_params: dict[str, Any] = field(
        default_factory=lambda: {"language": get_env_value("SUMMARY_LANGUAGE", "English", str)}
    )  # 额外参数【语言参数：当前lightrag默认“The same language like input text”】

    # Storages Management
    # ---

    _storages_status: StoragesStatus = field(default=StoragesStatus.NOT_CREATED)

    lightrag_logger: LightRAGLogger = field(default=create_lightrag_logger(workspace=workspace))

    def __post_init__(self):  # lightRag实例初始化后处理操作
        # -- 验证存储类型及存储实现类是否合法
        # Verify storage implementation compatibility and environment variables
        storage_configs = [
            ("KV_STORAGE", self.kv_storage),
            ("VECTOR_STORAGE", self.vector_storage),
            ("GRAPH_STORAGE", self.graph_storage),
        ]

        for storage_type, storage_name in storage_configs:
            # Verify storage implementation compatibility
            verify_storage_implementation(storage_type, storage_name)
        # -- 初始化分词器
        # Init Tokenizer
        # Post-initialization hook to handle backward compatabile tokenizer initialization based on provided parameters
        if self.tokenizer is None:
            if self.tiktoken_model_name:
                self.tokenizer = TiktokenTokenizer(self.tiktoken_model_name)
            else:
                self.tokenizer = TiktokenTokenizer()

        # Initialize all storages
        # 初始化存储实例
        self.key_string_value_json_storage_cls: type[BaseKVStorage] = self._get_storage_class(self.kv_storage)  # type: ignore
        self.vector_db_storage_cls: type[BaseVectorStorage] = self._get_storage_class(self.vector_storage)  # type: ignore
        self.graph_storage_cls: type[BaseGraphStorage] = self._get_storage_class(self.graph_storage)  # type: ignore
        self.key_string_value_json_storage_cls = partial(  # type: ignore
            self.key_string_value_json_storage_cls
        )
        self.vector_db_storage_cls = partial(  # type: ignore
            self.vector_db_storage_cls
        )
        self.graph_storage_cls = partial(  # type: ignore
            self.graph_storage_cls
        )
        # TODO: deprecating, text_chunks is redundant with chunks_vdb
        self.text_chunks: BaseKVStorage = self.key_string_value_json_storage_cls(  # type: ignore
            namespace=NameSpace.KV_STORE_TEXT_CHUNKS,  # text_chunks
            workspace=self.workspace,  # 知识库id
            embedding_func=self.embedding_func,
        )  # 见aperag.graph.lightrag.kg.pg_ops_sync_kv_storage.PGOpsSyncKVStorage
        self.chunk_entity_relation_graph: BaseGraphStorage = self.graph_storage_cls(  # type: ignore
            namespace=NameSpace.GRAPH_STORE_CHUNK_ENTITY_RELATION,
            workspace=self.workspace,
            embedding_func=self.embedding_func,
        )  # 见aperag.graph.lightrag.kg.pg_ops_sync_graph_storage.PGOpsSyncGraphStorage

        self.entities_vdb: BaseVectorStorage = self.vector_db_storage_cls(  # type: ignore
            namespace=NameSpace.VECTOR_STORE_ENTITIES,
            workspace=self.workspace,
            embedding_func=self.embedding_func,
            cosine_better_than_threshold=self.cosine_better_than_threshold,
            _max_batch_size=self.max_batch_size,
            meta_fields={"entity_name", "source_id", "content", "file_path"},
        )
        self.relationships_vdb: BaseVectorStorage = self.vector_db_storage_cls(  # type: ignore
            namespace=NameSpace.VECTOR_STORE_RELATIONSHIPS,
            workspace=self.workspace,
            embedding_func=self.embedding_func,
            cosine_better_than_threshold=self.cosine_better_than_threshold,
            _max_batch_size=self.max_batch_size,
            meta_fields={"src_id", "tgt_id", "source_id", "content", "file_path"},
        )
        self.chunks_vdb: BaseVectorStorage = self.vector_db_storage_cls(  # type: ignore
            namespace=NameSpace.VECTOR_STORE_CHUNKS,  # chunks
            workspace=self.workspace,  # 知识库id
            embedding_func=self.embedding_func,
            cosine_better_than_threshold=self.cosine_better_than_threshold,
            _max_batch_size=self.max_batch_size,
            meta_fields={"full_doc_id", "content", "file_path"},
        )  # 见aperag.graph.lightrag.kg.pg_ops_sync_vector_storage.PGOpsSyncVectorStorage
        # -- 初始化存储状态和日志实例
        self._storages_status = StoragesStatus.CREATED
        self.lightrag_logger = create_lightrag_logger(workspace=self.workspace)

    async def initialize_storages(self):
        """Asynchronously initialize the storages"""
        if self._storages_status == StoragesStatus.CREATED:
            tasks = []

            for storage in (
                self.text_chunks,
                self.entities_vdb,
                self.relationships_vdb,
                self.chunks_vdb,
                self.chunk_entity_relation_graph,
            ):
                if storage:
                    tasks.append(storage.initialize())

            await asyncio.gather(*tasks)

            self._storages_status = StoragesStatus.INITIALIZED
            logger.debug("Initialized Storages")

    async def finalize_storages(self):
        """Asynchronously finalize the storages"""
        if self._storages_status == StoragesStatus.INITIALIZED:
            tasks = []

            for storage in (
                self.text_chunks,
                self.entities_vdb,
                self.relationships_vdb,
                self.chunks_vdb,
                self.chunk_entity_relation_graph,
            ):
                if storage:
                    tasks.append(storage.finalize())

            await asyncio.gather(*tasks)

            self._storages_status = StoragesStatus.FINALIZED
            logger.debug("Finalized Storages")

    async def get_graph_labels(self):
        text = await self.chunk_entity_relation_graph.get_all_labels()
        return text

    async def get_knowledge_graph(
        self,
        node_label: str,
        max_depth: int = 3,
        max_nodes: int = 1000,
    ) -> KnowledgeGraph:  # 基于给定标签获取知识图谱
        """Get knowledge graph for a given label

        Args:
            node_label (str): Label to get knowledge graph for
            max_depth (int): Maximum depth of graph
            max_nodes (int, optional): Maximum number of nodes to return. Defaults to 1000.

        Returns:
            KnowledgeGraph: Knowledge graph containing nodes and edges
        """

        kg = await self.chunk_entity_relation_graph.get_knowledge_graph(node_label, max_depth, max_nodes)
        # -- 节点和边描述信息的格式处理【将分隔符标签替换为双换行符】
        # Clean up descriptions in nodes by replacing GRAPH_FIELD_SEP with double newlines
        if kg.nodes and len(kg.nodes) > 0:
            for node in kg.nodes:
                if node.properties.get("description"):
                    # Replace <SEP> with double newlines for better readability
                    node.properties["description"] = node.properties["description"].replace(GRAPH_FIELD_SEP, "\n\n")

        # Clean up descriptions in edges by replacing GRAPH_FIELD_SEP with double newlines
        if kg.edges and len(kg.edges) > 0:
            for edge in kg.edges:
                if edge.properties.get("description"):
                    # Replace <SEP> with double newlines for better readability
                    edge.properties["description"] = edge.properties["description"].replace(GRAPH_FIELD_SEP, "\n\n")

        return kg

    def _get_storage_class(self, storage_name: str) -> Callable[..., Any]:
        # Direct class lookup from registry instead of dynamic import
        storage_class = STORAGES[storage_name]
        return storage_class

    # ============= New Stateless Interfaces =============
    # TODO 为什么使用广度优先遍历获取单个文档知识图谱的所有连通分量，而不采用深度优先遍历
    """
    在图论中，**深度优先搜索（DFS）和广度优先搜索（BFS）都是计算连通分量的有效算法**，两者在正确性上没有本质区别，选择哪种算法更多取决于具体场景的需求（如性能、内存、结果顺序等）。上述代码采用BFS而非DFS，核心原因是**BFS在“实体关系图”这类场景下更契合实际需求，且在内存占用、结果可读性上有隐性优势**，具体可从以下角度分析：

    
    ### 一、先明确前提：DFS和BFS计算连通分量的“本质等价性”
    无论用DFS还是BFS，最终得到的连通分量结果**完全一致**——两者的核心逻辑都是“从一个未访问节点出发，遍历所有可达节点，形成一个连通分量”，区别仅在于“遍历节点的顺序”：
    - **DFS**：“深度优先”，优先遍历当前节点的“深层邻接节点”（比如从A→B→C，先走到最深处再回溯）；
    - **BFS**：“广度优先”，优先遍历当前节点的“所有直接邻接节点”（比如从A出发，先访问A的所有邻居，再访问邻居的邻居）。
    
    对于“计算连通分量”这一目标，两种算法的时间复杂度均为 **O(V+E)**（V是节点数，E是边数），效率在同一量级，不存在“谁更优”的绝对结论。
    
    
    ### 二、代码选择BFS的核心原因
    上述代码处理的是“实体关系图”（节点是实体，边是实体间的关联），这类场景的特点是“节点数通常适中、边的密度较低”，BFS在以下方面更契合需求：
    
    
    #### 1. 内存占用更可控（避免DFS的“递归栈溢出”风险）
    DFS的实现有两种方式：
    - **递归实现**：代码简洁，但依赖编程语言的“递归调用栈”——若实体关系图存在“深层链式结构”（如A→B→C→D→...→Z，共1000个节点），递归深度会达到1000，远超Python默认的递归栈深度（默认约1000，但实际业务中可能因其他调用占用栈空间，导致栈溢出）。
    - **迭代实现（用栈模拟）**：可避免栈溢出，但代码复杂度高于BFS（需手动维护栈的入栈/出栈顺序）。
    
    而BFS基于**队列（Queue）** 实现，队列的“先进先出”特性天然适合“逐层遍历”，且队列的内存占用与“当前层的节点数”相关（而非深度）。对于实体关系图，“同一层的节点数”通常远小于“图的最大深度”，内存占用更稳定，也无需担心栈溢出问题。
    
    **示例**：若实体图是一条1000节点的链式结构（A-B-C-...-Z）：
    - 递归DFS会因深度1000触发`RecursionError`；
    - BFS的队列最大长度始终为1（每层只有1个节点），内存占用极低。
    
    
    #### 2. 结果顺序更符合“实体关联的直观逻辑”
    在实体关系场景中，BFS的“逐层遍历”会优先将“直接关联的实体”归为一组，结果顺序更贴近人类对“关联关系”的直观理解。
    
    **示例**：实体关系为“用户A→订单B→商品C→品牌D”：
    - **BFS结果**：`[A, B, C, D]`（先A，再A的直接关联B，再B的直接关联C，最后C的直接关联D），顺序与“关联链路”一致，可读性高；
    - **DFS结果**：`[A, B, C, D]`（递归深度优先）或 `[A, B, D, C]`（迭代DFS，取决于栈的处理顺序），可能出现“跳层”，可读性稍差。
    
    对于后续的“实体聚类分析”“知识图谱展示”等场景，BFS的结果顺序更便于理解实体间的关联层级。
    
    #### 3. 代码实现更简洁（基于Python的列表模拟队列）
    在Python中，用列表的`append()`（入队）和`pop(0)`（出队，模拟队列的先进先出）可快速实现BFS，代码逻辑直观且不易出错：
    ```python
    queue = [node]  # 初始化队列
    while queue:
        current = queue.pop(0)  # 出队（队首）
        for neighbor in adjacency[current]:
            if neighbor not in visited:
                queue.append(neighbor)  # 入队（队尾）
    ```
    
    而DFS的迭代实现需要用列表模拟“栈”（`append()`入栈，`pop()`出栈，后进先出），代码逻辑虽不复杂，但需要额外注意“栈的处理顺序”，且容易与BFS的队列实现混淆（尤其是对不熟悉两种算法的开发者）。
    
    对于工具类代码（如上述`_find_connected_components`），“简洁性”和“可维护性”是重要考量，BFS的实现更符合这一需求。
        
    #### 4. 对“无向图”的适配性完全一致
    连通分量的计算通常基于**无向图**（实体关系是双向的，如“A关联B”等价于“B关联A”）。DFS和BFS对无向图的适配性没有差异，但BFS的“双向关联处理”更直接——无需担心“回溯时重复访问父节点”（因为`visited`集合会标记已访问节点，无论BFS还是DFS都能避免重复）。
        
    ### 三、什么时候会优先选择DFS？
    虽然上述代码选择了BFS，但在以下场景中，DFS可能更合适：
    1. **图的深度较小，但宽度极大**（如“一个中心节点关联1000个叶子节点”）：DFS的栈占用（最大深度2）远小于BFS的队列占用（最大宽度1000）；
    2. **需要快速找到“任意一条路径”**（如判断两个实体是否连通）：DFS通常能更快找到一条路径（无需遍历所有同层节点）；
    3. **递归实现更简洁且图深度可控**（如小规模实体图，深度不超过100）：DFS的递归代码（几行即可实现）比BFS更简洁。
    
    但这些场景在“实体关系图”中并不常见——实体关系图通常不会出现“单个节点关联上千个邻居”的极端情况，且深度可能较大（如“用户→订单→商品→品牌→厂商”的多层级关联），因此BFS是更稳妥的选择。
    
    ### 总结
    上述代码选择BFS而非DFS，并非因为DFS“不正确”或“效率低”，而是基于**实体关系图的场景特性**和**工程实现的实用性**：
    - 避免递归栈溢出，内存占用更可控；
    - 结果顺序更符合实体关联的直观逻辑；
    - 代码实现简洁，可维护性高。
    
    本质上，这是“算法选择适配具体场景”的典型案例——两种算法在理论上等价，但在工程实践中需结合数据结构特点、语言特性和业务需求做取舍。
    """
    def _find_connected_components(self, chunk_results: List[tuple[dict, dict]]) -> List[List[str]]:  # 通过图论中的 “广度优先搜索（BFS）” 算法，将相互关联的实体归类为一组，实现实体的 “聚类分组”
        """
        当前方法的本质是实体关系的 “聚类” 工具，其价值在于：
            - 将分散在不同文档分段中的实体，通过关系关联起来，形成 “语义闭环” 的实体组（例如 “人物 A - 公司 B - 产品 C” 因存在雇佣、生产关系而被归为一组）。
            - 为后续的知识图谱构建、实体关联分析、问答系统等提供基础（例如回答 “与 A 相关的所有实体有哪些” 时，可直接返回其所在连通组件的实体）。
        """
        """
        Find connected components in the extracted entities and relationships.

        Args:
            chunk_results: List of (nodes_dict, edges_dict) tuples from entity extraction
            实体关系提取结果形如：[分段1的实体关系信息【形如：{实体名称1：实体名称1的实体信息列表}， {(源实体名称1，目标实体名称1)：相应起止实体名称的边信息列表}】]
            实体信息：【内含：实体名称、实体类型、实体描述、分段id和原始文档路径】
            关系信息：【内含：源节点id【源实体名称】、目标节点id【目标实体名称】、权重、边描述【关系描述】、边关键词【关系关键词】、来源id【分段id】、原始文档路径】

        Returns:
            List of entity groups, where each group is a list of connected entity names
        """
        # -- 基于实体和关系构造图【单个文档】【邻接字典方式】【注意所有实体都在其keys中】
        # 初始化邻接字典【图的表示方式】
        # Build adjacency list
        adjacency: Dict[str, set[str]] = {}
        # 将所有实体和所有边的起止实体添加到邻接字典的keys中，相应key的值为“以该key【实体/节点】为起点的边的终点实体/节点”集合
        for nodes, edges in chunk_results:  # 逐个分段处理其实体关系数据
            # Add all nodes to adjacency list
            # 将所有实体添加到邻接字典中
            for entity_name in nodes.keys():
                if entity_name not in adjacency:
                    adjacency[entity_name] = set()

            # Add edges to create connections
            # 将所有关系的起止实体添加到邻接字典中
            for src, tgt in edges.keys():
                if src not in adjacency:
                    adjacency[src] = set()
                if tgt not in adjacency:
                    adjacency[tgt] = set()
                adjacency[src].add(tgt)
                adjacency[tgt].add(src)
        # -- 基于广度优先算法寻找所有“相互关联的”实体连通组件【与图的连通分量概念一致】 TODO 【在知识图谱场景中，每个连通组件可对应一个 “子知识图谱”，便于聚焦分析某一主题的相关实体】
        """
        连通分量的概念：  
            图的一个节点子集合，满足两个条件：
                - 子集合内的任意两个节点（顶点）之间，都存在至少一条路径（通过边连接）；
                - 子集合外的任何节点，都无法通过边与子集合内的节点连通。
        
        简单来说：“连通分量” 是图中 “相互可达的节点集群”，集群内部节点彼此连通，集群之间完全孤立。
        """
        """
                功能示例：
                若邻接字典为 {"A": {"B"}, "B": {"A", "C"}, "C": {"B"}, "D": {}}，则 BFS 过程为：

                    从 “A” 开始：访问 A → 发现邻接 B → 访问 B → 发现邻接 C → 访问 C → 无新实体，组件为 ["A", "B", "C"]。
                    从 “D” 开始：D 无邻接实体，组件为 ["D"]。
                    最终 components = [["A", "B", "C"], ["D"]]。
                """
        # Find connected components using BFS
        visited = set()  # 记录已访问过的实体（避免重复处理）
        components = []  # 初始化实体组列表，用以存储所有连通组件
        # 遍历图中所有实体
        for node in adjacency:
            if node not in visited:  # 若当前实体未被访问过，说明它是新连通组件的起点
                # Start BFS from this node
                component = []  # 初始化当前实体组，用以存储当前连通组件的实体
                queue = [node]  # BFS队列，初始包含起点实体
                visited.add(node)  # 标记为当前实体已访问
                # 执行BFS：逐层访问所有关联的实体
                while queue:
                    current = queue.pop(0)  # 取出队列中的第一个实体
                    component.append(current)  # 将当前实体加入组件
                    # 遍历当前实体的所有邻接实体【“邻居”的含义对应BFS中的广度优先遍历的“层”的概念】
                    # Visit all neighbors
                    for neighbor in adjacency.get(current, set()):
                        if neighbor not in visited:  # 若邻接实体未被访问
                            visited.add(neighbor)  # 将当前邻接实体标记为已访问
                            queue.append(neighbor)  # 将当前邻接实体加入队列，等待后续访问
                # 当BFS结束时，component中就是一个完整的连通组件
                components.append(component)  # 收集当前连通组件

        self.lightrag_logger.debug(f"Found {len(components)} connected components from {len(adjacency)} entities")
        return components

    async def _grouping_process_chunk_results(
        self,
        chunk_results: List[tuple[dict, dict]],  # 实体关系提取结果形如：[分段1的实体关系信息【形如：{实体名称1：实体名称1的实体信息列表}， {(源实体名称1，目标实体名称1)：相应起止实体名称的边信息列表}】]
        collection_id: str | None = None,  # 知识库id
    ) -> dict[str, Any]:
        """
        实体信息：【内含：实体名称、实体类型、实体描述、分段id和原始文档路径】
        关系信息：【内含：源节点id【源实体名称】、目标节点id【目标实体名称】、权重、边描述【关系描述】、边关键词【关系关键词】、来源id【分段id】、原始文档路径】
        """
        """
        Process entities and relationships in groups based on connected components.

        Args:
            chunk_results: List of (nodes_dict, edges_dict) from entity extraction
            collection_id: Optional collection ID for logging

        Returns:
            Dict with processing results
        """
        # -- 基于广度优先遍历算法获取单个文档知识图谱的所有连通分量
        components = self._find_connected_components(chunk_results)  # 获取单个文档知识图谱的所有连通分量

        # Handle case where no entities were extracted
        if not components:  # 如果连通组件列表为空，说明所有实体相互独立，则知识图谱无效，返回0实体-0关系-0连通分量
            self.lightrag_logger.info("No entities or relationships extracted - returning success with zero counts")
            return {
                "groups_processed": 0,  # 连通分量个数
                "total_entities": 0,
                "total_relations": 0,
                "collection_id": collection_id,
            }
        # -- 整理所有连通组件任务参数，形成任务参数列表
        # Prepare component data for parallel processing
        component_tasks = []  # 初始化连通组件任务参数列表

        for i, component in enumerate(components):
            # Create a set for quick lookup
            component_entities = set(component)  # 对当前连通组件进行实体去重

            # Filter chunk results for this component
            component_chunk_results = []  # 元组列表，当前连通组件对应的实体关系数据列表，形如[(分段1的属于当前连通组件的实体数据【字典，形如：{实体1：实体1数据}】，分段1的属于当前连通组件的关系数据【字典，形如：{(起始实体1，目标实体1)：对应边数据}】)]
            # 从全量实体和关系数据中提取属于当前连通组件的实体和关系
            for nodes, edges in chunk_results:
                # Filter nodes belonging to this component
                filtered_nodes = {
                    entity_name: entity_data
                    for entity_name, entity_data in nodes.items()
                    if entity_name in component_entities
                }

                # Filter edges where both endpoints belong to this component
                filtered_edges = {
                    (src, tgt): edge_data
                    for (src, tgt), edge_data in edges.items()
                    if src in component_entities and tgt in component_entities
                }

                if filtered_nodes or filtered_edges:  # 实体或关系非空时，才会收集
                    component_chunk_results.append((filtered_nodes, filtered_edges))
            # 当前连通组件对应的实体关系为空时，跳过
            if not component_chunk_results:
                continue
            # 将当前连通组件及其实体关系作为任务参数，放入连通组件任务参数列表中
            # Add task data for this component
            component_tasks.append(
                {
                    "index": i,
                    "component": component,  # 当前连通组件中包含的实体列表
                    "component_chunk_results": component_chunk_results,  # 元组列表，当前连通组件对应的实体关系数据列表，形如[(分段1的属于当前连通组件的实体数据【字典，形如：{实体1：实体1数据}】，分段1的属于当前连通组件的关系数据【字典，形如：{(起始实体1，目标实体1)：对应边数据}】)]
                    "total_components": len(components),  # 连通组件总量【单个文档】
                }
            )
        # -- 异步处理连通组件任务
        # ---- 基于信号量控制并发执行异步任务数上限为1
        # Process components concurrently with semaphore
        semaphore = asyncio.Semaphore(1)

        async def _process_component_with_semaphore(task_data):  # 处理单个连通组件任务 TODO 【持久化操作？】
            """
            task_data形如：
            {
                    "index": i,
                    "component": component,  # 当前连通组件中包含的实体列表
                    "component_chunk_results": component_chunk_results,  # 元组列表，当前连通组件对应的实体关系数据列表，形如[(分段1的属于当前连通组件的实体数据【字典，形如：{实体1：实体1数据}】，分段1的属于当前连通组件的关系数据【字典，形如：{(起始实体1，目标实体1)：对应边数据}】)]
                    "total_components": len(components),  # 连通组件总量【单个文档】
                }
            """
            async with semaphore:
                self.lightrag_logger.debug(
                    f"Processing component {task_data['index'] + 1}/{task_data['total_components']} "
                    f"with {len(task_data['component'])} entities"
                )

                # Call merge_nodes_and_edges with component information
                result = await merge_nodes_and_edges(
                    chunk_results=task_data["component_chunk_results"],  # 元组列表，当前连通组件对应的实体关系数据列表，形如[(分段1的属于当前连通组件的实体数据【字典，形如：{实体1：实体1数据}】，分段1的属于当前连通组件的关系数据【字典，形如：{(起始实体1，目标实体1)：对应边数据}】)]
                    component=task_data["component"],  # 当前连通组件中包含的实体列表
                    workspace=self.workspace,  # 知识库id
                    knowledge_graph_inst=self.chunk_entity_relation_graph,  # 知识图谱存储实例，见aperag.graph.lightrag.kg.pg_ops_sync_graph_storage.PGOpsSyncGraphStorage
                    entity_vdb=self.entities_vdb,  # 实体存储实例，见aperag.graph.lightrag.kg.pg_ops_sync_vector_storage.PGOpsSyncVectorStorage
                    relationships_vdb=self.relationships_vdb,  # 关系存储实例，见aperag.graph.lightrag.kg.pg_ops_sync_vector_storage.PGOpsSyncVectorStorage
                    llm_model_func=self.llm_model_func,  # llm操作定义
                    tokenizer=self.tokenizer,  # 分词器
                    llm_model_max_token_size=self.llm_model_max_token_size,
                    summary_to_max_tokens=self.summary_to_max_tokens,
                    addon_params=self.addon_params or PROMPTS["DEFAULT_LANGUAGE"],
                    force_llm_summary_on_merge=self.force_llm_summary_on_merge,
                    lightrag_logger=self.lightrag_logger,
                )  # TODO 至此~

                self.lightrag_logger.debug(
                    f"Completed component {task_data['index'] + 1}: "
                    f"{result['entity_count']} entities, {result['relation_count']} relations"
                )

                return result
        # ---- 创建连通组件任务列表
        # Create tasks for concurrent processing
        tasks = []
        for task_data in component_tasks:
            task = asyncio.create_task(_process_component_with_semaphore(task_data))
            tasks.append(task)

        # Handle case where no valid component tasks were created
        if not tasks:  # 连通组件任务列表为空，直接返回0实体-0关系-0连通分量
            self.lightrag_logger.info("No valid component tasks created - returning success with zero counts")
            return {
                "groups_processed": 0,
                "total_entities": 0,
                "total_relations": 0,
                "collection_id": collection_id,
            }
        # ---- 等待任务执行：优先处理第一个异常
        # Wait for all tasks to complete or for the first exception
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)
        # ---- 异常处理：终止所有任务并传播异常
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
        # ---- 收集结果：所有任务成功时汇总结果
        # Collect results from all tasks
        results = [task.result() for task in tasks]

        # Calculate totals
        total_entities = sum(r["entity_count"] for r in results)
        total_relations = sum(r["relation_count"] for r in results)
        processed_groups = len(results)

        return {
            "groups_processed": processed_groups,  # 成功处理的连通组件个数
            "total_entities": total_entities,  # 实体总量
            "total_relations": total_relations,  # 关系总量
            "collection_id": collection_id,  # 知识库id
        }

    async def ainsert_and_chunk_document(
        self,
        documents: list[str],
        doc_ids: list[str] | None = None,
        file_paths: list[str] | None = None,
        split_by_character: str | None = None,
        split_by_character_only: bool = False,
    ) -> dict[str, Any]:  # 分段、保存分段【进行了embedding处理】、返回分段结果【内含：分段id，分段内容，分段长度，分段在整个markdown文本中的索引顺序】
        """
        Stateless document insertion and chunking - inserts documents and performs chunking in one step.

        Args:
            documents: List of document contents
            doc_ids: Optional list of document IDs (will generate if not provided)
            file_paths: Optional list of file paths for citation
            split_by_character: Optional character to split by
            split_by_character_only: If True, only split by character

        Returns:
            Dict with document metadata and chunks
        """
        # -- 列表化
        # Ensure lists
        if isinstance(documents, str):
            documents = [documents]
        if isinstance(doc_ids, str):
            doc_ids = [doc_ids]
        if isinstance(file_paths, str):
            file_paths = [file_paths]
        # -- 文档参数长度一致性验证
        # Validate inputs
        if file_paths and len(file_paths) != len(documents):
            raise ValueError("Number of file paths must match number of documents")
        if doc_ids and len(doc_ids) != len(documents):
            raise ValueError("Number of doc IDs must match number of documents")
        # -- 文档路径为空或者文档id为空时的自动生成操作
        # Use default file paths if not provided
        if not file_paths:
            file_paths = ["unknown_source"] * len(documents)

        # Generate or validate IDs
        if not doc_ids:
            doc_ids = [compute_mdhash_id(clean_text(doc), prefix="doc-", workspace=self.workspace) for doc in documents]
        else:
            # Check uniqueness
            if len(doc_ids) != len(set(doc_ids)):
                raise ValueError("Document IDs must be unique")
        # -- 分段处理
        results = []

        for doc_id, content, file_path in zip(doc_ids, documents, file_paths):
            cleaned_content = clean_text(content)  # 删除文本两侧的空格和文本中的空字节（0x00）

            if not cleaned_content.strip():  # 文本非空校验
                raise ValueError(f"Document {doc_id} content is empty after cleaning")

            # Perform chunking
            """
            分段列表结果形如：
            [
                {
                    "tokens": min(max_token_size, len(tokens) - start),  # 分段长度
                    "content": chunk_content.strip(),  # 分段内容
                    "chunk_order_index": index,  # 分段的索引【相对整个文档的content而言】
                }
            ]
            """
            chunk_list = self.chunking_func(
                self.tokenizer,  # 分词器
                cleaned_content,  # 文本内容
                split_by_character,  # 分隔符，这里为None
                split_by_character_only,  # False
                self.chunk_overlap_token_size,  # 分段间重叠token数量，100
                self.chunk_token_size,  # 分段token数量，1200
            )  # 基于分词器、分段参数进行分段处理
            # -- 验证分段列表结果格式并构造分段字典
            # Validate chunk_list format
            if not chunk_list:  # 非空校验
                raise ValueError(f"Chunking returned empty list for document {doc_id}")

            # Create chunk data with IDs and validate each chunk
            chunks = {}
            for i, chunk_data in enumerate(chunk_list):  # 逐个分段数据校验，校验通过时，基于分段内容生成相应分段id，并【分段id：分段数据【字典形式】】收集到分段字典中
                # Validate chunk_data format
                if not isinstance(chunk_data, dict):
                    raise ValueError(f"Chunk {i} is not a dictionary: {type(chunk_data)}")
                if "content" not in chunk_data:
                    raise ValueError(f"Chunk {i} missing 'content' key: {chunk_data.keys()}")
                if not chunk_data["content"]:
                    logger.warning(f"Chunk {i} has empty content, skipping")
                    continue

                chunk_id = compute_mdhash_id(chunk_data["content"], prefix="chunk-", workspace=self.workspace)
                chunks[chunk_id] = {
                    **chunk_data,
                    "full_doc_id": doc_id,
                    "file_path": file_path,
                }

            if not chunks:
                raise ValueError(f"No valid chunks created for document {doc_id}")
            # -- 保存分段数据【同一张表lightrag_doc_chunks，执行了两次保存或更新操作】
            # Write to storage (avoid concurrent operations on same connection)
            self.lightrag_logger.debug(f"LightRAG: About to upsert {len(chunks)} chunks to storages")
            self.lightrag_logger.debug(f"LightRAG: Calling chunks_vdb.upsert with {len(chunks)} chunks")
            # 将分段数据分批embedding处理后，连同embedding结果保存或更新至数据库
            await self.chunks_vdb.upsert(chunks)  # 存储实例见aperag.graph.lightrag.kg.pg_ops_sync_vector_storage.PGOpsSyncVectorStorage
            self.lightrag_logger.debug(f"LightRAG: Calling text_chunks.upsert with {len(chunks)} chunks")
            # 直接保存或更新分段数据【不含embedding处理】
            await self.text_chunks.upsert(chunks)  # 存储实例见aperag.graph.lightrag.kg.pg_ops_sync_kv_storage.PGOpsSyncKVStorage
            self.lightrag_logger.debug(f"LightRAG: Completed all upsert operations for {doc_id}")

            self.lightrag_logger.debug(f"Inserted and chunked document {doc_id}: {len(chunks)} chunks")

            results.append(
                {
                    "doc_id": doc_id,  # 原始文档id
                    "chunks": list(chunks.keys()),  # 分段id列表
                    "chunk_count": len(chunks),  # 分段数量
                    "chunks_data": chunks,  # 分段数据详情【内含：分段id，分段内容，分段长度，分段在整个markdown文本中的索引顺序】
                    "status": "processed",
                }
            )

        return {
            "results": results,
            "total_documents": len(doc_ids),
            "total_chunks": sum(len(r["chunks"]) for r in results),
            "status": "success",
        }

    async def aprocess_graph_indexing(
        self,
        chunks: dict[str, Any],
        collection_id: str | None = None,
    ) -> dict[str, Any]:  # 对单个文档的分段数据，构建知识图谱
        """
        Stateless graph indexing - extracts entities/relations and builds graph index.

        Args:
            chunks: Dict of chunk_id -> chunk_data
            collection_id: Optional collection ID for logging

        Returns:
            Dict with extraction results
        """

        try:
            # -- 分段数据非空及合法性校验
            # Validate chunks input
            if not chunks:
                raise ValueError("No chunks provided for graph indexing")

            # Validate each chunk has required fields
            for chunk_id, chunk_data in chunks.items():  # 任一个分段数据不合法，都会触发异常
                if not isinstance(chunk_data, dict):  # 单个分段数据详情必为字典
                    raise ValueError(f"Chunk {chunk_id} is not a dictionary")
                if "content" not in chunk_data:  # 单个分段数据详情必为含有content字段【分段内容】
                    raise ValueError(f"Chunk {chunk_id} missing 'content' key")
                if not chunk_data["content"]:  # 分段内容非空
                    raise ValueError(f"Chunk {chunk_id} has empty content")

            self.lightrag_logger.debug(f"Starting graph indexing for {len(chunks)} chunks")
            # -- 对分段数据提取实体和关系【采用了：异步并发执行、基于信号量的最大并发数控制、异步任务首次异常处理】
            # 1. Extract entities and relations from chunks (completely parallel, no lock)
            chunk_results = await extract_entities(
                chunks,  # 单个文档的分段数据详情
                use_llm_func=self.llm_model_func,  # llm操作定义
                entity_extract_max_gleaning=self.entity_extract_max_gleaning,  # 对不明确的内容尝试提取实体的最大次数【当前lightrag中默认0次】
                addon_params=self.addon_params,  # 额外参数【语言参数：当前lightrag默认“The same language like input text”】
                llm_model_max_async=self.llm_model_max_async,  # llm操作最大并发调用数
                lightrag_logger=self.lightrag_logger,  # lightrag日志实例
            )  # 实体关系结果形如：[分段1的实体关系信息【形如：{实体名称1：实体名称1的实体信息列表}， {(源实体名称1，目标实体名称1)：相应起止实体名称的边信息列表}】]
            # -- 基于提取的实体关系数据，基于广度优先算法提取所有连通组件，【基于连通组件进行图谱有效性校验，若所有实体相互独立，则说明没必要构建知识图谱了】，异步处理连通组件任务
            # 2. Process each component group with its own lock scope
            result = await self._grouping_process_chunk_results(chunk_results, collection_id)
            # -- 汇总知识图谱构建结果
            # Count total results
            entity_count = sum(len(nodes) for nodes, _ in chunk_results)  # 实体总量
            relation_count = sum(len(edges) for _, edges in chunk_results)  # 关系总量

            self.lightrag_logger.info(
                f"Graph indexing completed: {entity_count} entities, {relation_count} relations "
                f"in {result['groups_processed']} groups"
            )  # lightrag日志打印

            return {
                "status": "success",  # 知识图谱构建成功
                "chunks_processed": len(chunks),  # 已处理的分段数量
                "entities_extracted": entity_count,  # 提取的实体总量
                "relations_extracted": relation_count,  # 提取的关系总量
                "groups_processed": result["groups_processed"],  #
                "collection_id": collection_id,  # 知识库id
            }

        except Exception as e:
            if "lightrag_logger" in locals():
                self.lightrag_logger.error(f"Graph indexing failed: {str(e)}")
            else:
                logger.error(f"Graph indexing failed: {str(e)}", exc_info=True)
            raise e

    # ============= End of New Stateless Interfaces =============

    async def aquery_context(
        self,
        query: str,
        param: QueryParam = QueryParam(),
    ):
        param.original_query = query
        context_data = await build_query_context(
            query.strip(),
            self.chunk_entity_relation_graph,
            self.entities_vdb,
            self.relationships_vdb,
            self.text_chunks,
            param,
            self.tokenizer,
            self.llm_model_func,
            self.addon_params,
            chunks_vdb=self.chunks_vdb,
        )

        if context_data is None:
            return ""

        entities_context, relations_context, text_units_context = context_data

        # Remove file_path from all contexts before serialization
        def remove_file_path_from_context(context_list):
            """Remove file_path field from each item in the context list"""
            if not context_list:
                return context_list

            cleaned_context = []
            for item in context_list:
                if isinstance(item, dict) and "file_path" in item:
                    # Create a copy without file_path
                    cleaned_item = {k: v for k, v in item.items() if k != "file_path"}
                    cleaned_context.append(cleaned_item)
                else:
                    cleaned_context.append(item)
            return cleaned_context

        # Clean all contexts
        entities_context = remove_file_path_from_context(entities_context)
        relations_context = remove_file_path_from_context(relations_context)
        text_units_context = remove_file_path_from_context(text_units_context)

        import json

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
        return context

    async def aquery(
        self,
        query: str,
        param: QueryParam = QueryParam(),
        system_prompt: str | None = None,
    ) -> str | AsyncIterator[str] | Tuple[dict, dict, dict]:
        """
        Perform a async query.

        Args:
            query (str): The query to be executed.
            param (QueryParam): Configuration parameters for query execution.
                If param.model_func is provided, it will be used instead of the global model.
            prompt (Optional[str]): Custom prompts for fine-tuned control over the system's behavior. Defaults to None, which uses PROMPTS["rag_response"].

        Returns:
            str: The result of the query execution.
        """
        # If a custom model is provided in param, temporarily update global config
        # Save original query for vector search
        param.original_query = query

        if param.mode in ["local", "global", "hybrid", "mix"]:
            response = await kg_query(
                query.strip(),
                self.chunk_entity_relation_graph,
                self.entities_vdb,
                self.relationships_vdb,
                self.text_chunks,
                param,
                self.tokenizer,
                self.llm_model_func,
                self.addon_params,
                system_prompt=system_prompt,
                chunks_vdb=self.chunks_vdb,
            )
        elif param.mode == "naive":
            response = await naive_query(
                query.strip(),
                self.chunks_vdb,
                param,
                self.llm_model_func,
                self.tokenizer,
                system_prompt=system_prompt,
            )
        elif param.mode == "bypass":
            # Bypass mode: directly use LLM without knowledge retrieval

            param.stream = True if param.stream is None else param.stream
            response = await self.llm_model_func(
                query.strip(),
                system_prompt=system_prompt,
                history_messages=param.conversation_history,
                stream=param.stream,
            )
        else:
            raise ValueError(f"Unknown mode {param.mode}")
        return response

    # Deleting documents can cause hallucinations in RAG.
    async def adelete_by_doc_id(self, doc_id: str) -> None:
        """Delete a document and all its related data

        Args:
            doc_id: Document ID to delete
        """
        try:
            self.lightrag_logger.info(f"Starting deletion for document {doc_id}")

            # ========== STEP 1: Get all chunks related to this document ==========
            all_chunks = await self.text_chunks.get_all()
            related_chunks = {
                chunk_id: chunk_data
                for chunk_id, chunk_data in all_chunks.items()
                if isinstance(chunk_data, dict) and chunk_data.get("full_doc_id") == doc_id
            }

            if not related_chunks:
                logger.warning(f"No chunks found for document {doc_id}")
                return

            chunk_ids = set(related_chunks.keys())
            self.lightrag_logger.info(f"Found {len(chunk_ids)} chunks to delete for document {doc_id}")

            # ========== STEP 2: Handle Vector Storage References (chunk_ids arrays) ==========
            # Process entities in vector storage
            entities_to_delete_from_vdb = []
            entities_to_update_in_vdb = {}

            if hasattr(self.entities_vdb, "get_all"):
                all_entities = await self.entities_vdb.get_all()
                for entity_id, entity_data in all_entities.items():
                    if not isinstance(entity_data, dict) or "chunk_ids" not in entity_data:
                        continue

                    # Remove deleted chunks from entity's chunk_ids array
                    old_chunk_ids = set(entity_data.get("chunk_ids", []))
                    new_chunk_ids = old_chunk_ids - chunk_ids

                    if not new_chunk_ids:
                        # Entity has no remaining chunks, mark for deletion
                        entity_name = entity_data.get("entity_name")
                        if entity_name:
                            entities_to_delete_from_vdb.append(entity_name)
                            self.lightrag_logger.debug(
                                f"Entity {entity_name} marked for deletion from VDB - no remaining chunks"
                            )
                    elif len(new_chunk_ids) != len(old_chunk_ids):
                        # Entity has some remaining chunks, update chunk_ids array
                        entity_data["chunk_ids"] = list(new_chunk_ids)
                        entity_data["source_id"] = GRAPH_FIELD_SEP.join(new_chunk_ids)
                        entities_to_update_in_vdb[entity_id] = entity_data
                        self.lightrag_logger.debug(
                            f"Entity {entity_data.get('entity_name')} chunk_ids updated: {len(old_chunk_ids)} -> {len(new_chunk_ids)}"
                        )

            # Process relationships in vector storage
            relationships_to_delete_from_vdb = []
            relationships_to_update_in_vdb = {}

            if hasattr(self.relationships_vdb, "get_all"):
                all_relationships = await self.relationships_vdb.get_all()
                for rel_id, rel_data in all_relationships.items():
                    if not isinstance(rel_data, dict) or "chunk_ids" not in rel_data:
                        continue

                    # Remove deleted chunks from relationship's chunk_ids array
                    old_chunk_ids = set(rel_data.get("chunk_ids", []))
                    new_chunk_ids = old_chunk_ids - chunk_ids

                    if not new_chunk_ids:
                        # Relationship has no remaining chunks, mark for deletion by calculating IDs
                        src_id = rel_data.get("src_id") or rel_data.get("source_id")
                        tgt_id = rel_data.get("tgt_id") or rel_data.get("target_id")
                        if src_id and tgt_id:
                            relationships_to_delete_from_vdb.append((src_id, tgt_id))
                            self.lightrag_logger.debug(
                                f"Relationship {src_id}-{tgt_id} marked for deletion from VDB - no remaining chunks"
                            )
                    elif len(new_chunk_ids) != len(old_chunk_ids):
                        # Relationship has some remaining chunks, update chunk_ids array
                        rel_data["chunk_ids"] = list(new_chunk_ids)
                        rel_data["source_id"] = GRAPH_FIELD_SEP.join(new_chunk_ids)
                        relationships_to_update_in_vdb[rel_id] = rel_data
                        self.lightrag_logger.debug(
                            f"Relationship {rel_data.get('src_id')}-{rel_data.get('tgt_id')} chunk_ids updated: {len(old_chunk_ids)} -> {len(new_chunk_ids)}"
                        )

            # ========== STEP 3: Handle Graph Storage References (source_id strings) ==========
            # Process entities in graph storage
            entities_to_delete_from_graph = set()
            entities_to_update_in_graph = {}

            # Process relationships in graph storage
            relationships_to_delete_from_graph = set()
            relationships_to_update_in_graph = {}

            # Get all labels from graph storage
            all_labels = await self.chunk_entity_relation_graph.get_all_labels()

            # Process each entity node
            for node_label in all_labels:
                node_data = await self.chunk_entity_relation_graph.get_node(node_label)
                if node_data and "source_id" in node_data:
                    # Parse source_id string (format: chunk1|chunk2|chunk3)
                    sources = set(node_data["source_id"].split(GRAPH_FIELD_SEP))
                    sources.difference_update(chunk_ids)

                    if not sources:
                        # Entity has no remaining source chunks
                        entities_to_delete_from_graph.add(node_label)
                        self.lightrag_logger.debug(
                            f"Entity {node_label} marked for deletion from graph - no remaining sources"
                        )
                    else:
                        # Entity has some remaining source chunks
                        new_source_id = GRAPH_FIELD_SEP.join(sources)
                        entities_to_update_in_graph[node_label] = new_source_id
                        self.lightrag_logger.debug(f"Entity {node_label} source_id will be updated in graph")

                # Process relationships for this entity
                node_edges = await self.chunk_entity_relation_graph.get_node_edges(node_label)
                if node_edges:
                    for src, tgt in node_edges:
                        edge_data = await self.chunk_entity_relation_graph.get_edge(src, tgt)
                        if edge_data and "source_id" in edge_data:
                            # Parse source_id string (format: chunk1|chunk2|chunk3)
                            sources = set(edge_data["source_id"].split(GRAPH_FIELD_SEP))
                            sources.difference_update(chunk_ids)

                            if not sources:
                                # Relationship has no remaining source chunks
                                relationships_to_delete_from_graph.add((src, tgt))
                                self.lightrag_logger.debug(
                                    f"Relationship {src}-{tgt} marked for deletion from graph - no remaining sources"
                                )
                            else:
                                # Relationship has some remaining source chunks
                                new_source_id = GRAPH_FIELD_SEP.join(sources)
                                relationships_to_update_in_graph[(src, tgt)] = new_source_id
                                self.lightrag_logger.debug(
                                    f"Relationship {src}-{tgt} source_id will be updated in graph"
                                )

            # ========== STEP 4: Execute all deletions and updates ==========

            # 4.1 Delete and update entities in vector storage
            if entities_to_delete_from_vdb:
                for entity_name in entities_to_delete_from_vdb:
                    await self.entities_vdb.delete_entity(entity_name)
                self.lightrag_logger.info(f"Deleted {len(entities_to_delete_from_vdb)} entities from vector storage")

            if entities_to_update_in_vdb:
                await self.entities_vdb.upsert(entities_to_update_in_vdb)
                self.lightrag_logger.info(f"Updated {len(entities_to_update_in_vdb)} entities in vector storage")

            # 4.2 Delete and update relationships in vector storage
            if relationships_to_delete_from_vdb:
                rel_ids_to_delete = []
                for src, tgt in relationships_to_delete_from_vdb:
                    rel_id_0 = compute_mdhash_id(src + tgt, prefix="rel-", workspace=self.workspace)
                    rel_id_1 = compute_mdhash_id(tgt + src, prefix="rel-", workspace=self.workspace)
                    rel_ids_to_delete.extend([rel_id_0, rel_id_1])
                await self.relationships_vdb.delete(rel_ids_to_delete)
                self.lightrag_logger.info(
                    f"Deleted {len(relationships_to_delete_from_vdb)} relationships from vector storage"
                )

            if relationships_to_update_in_vdb:
                await self.relationships_vdb.upsert(relationships_to_update_in_vdb)
                self.lightrag_logger.info(
                    f"Updated {len(relationships_to_update_in_vdb)} relationships in vector storage"
                )

            # 4.3 Delete and update entities in graph storage
            if entities_to_delete_from_graph:
                await self.chunk_entity_relation_graph.remove_nodes(list(entities_to_delete_from_graph))
                self.lightrag_logger.info(f"Deleted {len(entities_to_delete_from_graph)} entities from graph storage")

            for entity_name, new_source_id in entities_to_update_in_graph.items():
                node_data = await self.chunk_entity_relation_graph.get_node(entity_name)
                if node_data:
                    node_data["source_id"] = new_source_id
                    await self.chunk_entity_relation_graph.upsert_node(entity_name, node_data)
            if entities_to_update_in_graph:
                self.lightrag_logger.info(f"Updated {len(entities_to_update_in_graph)} entities in graph storage")

            # 4.4 Delete and update relationships in graph storage
            if relationships_to_delete_from_graph:
                await self.chunk_entity_relation_graph.remove_edges(list(relationships_to_delete_from_graph))
                self.lightrag_logger.info(
                    f"Deleted {len(relationships_to_delete_from_graph)} relationships from graph storage"
                )

            for (src, tgt), new_source_id in relationships_to_update_in_graph.items():
                edge_data = await self.chunk_entity_relation_graph.get_edge(src, tgt)
                if edge_data:
                    edge_data["source_id"] = new_source_id
                    await self.chunk_entity_relation_graph.upsert_edge(src, tgt, edge_data)
            if relationships_to_update_in_graph:
                self.lightrag_logger.info(
                    f"Updated {len(relationships_to_update_in_graph)} relationships in graph storage"
                )

            # 4.5 Finally, delete the chunks themselves
            await self.chunks_vdb.delete(list(chunk_ids))
            await self.text_chunks.delete(list(chunk_ids))
            self.lightrag_logger.info(f"Deleted {len(chunk_ids)} chunks from storages")

            # ========== STEP 5: Simple verification ==========
            # Verify chunks were actually deleted
            remaining_chunks = await self.text_chunks.get_all()
            remaining_related_chunks = {
                chunk_id: chunk_data
                for chunk_id, chunk_data in remaining_chunks.items()
                if isinstance(chunk_data, dict) and chunk_data.get("full_doc_id") == doc_id
            }

            if remaining_related_chunks:
                self.lightrag_logger.warning(
                    f"Verification failed: {len(remaining_related_chunks)} chunks still exist for document {doc_id}"
                )
            else:
                self.lightrag_logger.info(
                    f"Verification successful: All chunks for document {doc_id} have been deleted"
                )

            self.lightrag_logger.info(
                f"Document deletion completed for {doc_id}. "
                f"Summary: {len(chunk_ids)} chunks, "
                f"{len(entities_to_delete_from_vdb)} entities deleted from VDB, "
                f"{len(relationships_to_delete_from_vdb)} relationships deleted from VDB, "
                f"{len(entities_to_delete_from_graph)} entities deleted from graph, "
                f"{len(relationships_to_delete_from_graph)} relationships deleted from graph."
            )

        except Exception as e:
            self.lightrag_logger.error(f"Error while deleting document {doc_id}: {e}")
            raise

    async def agenerate_merge_suggestions(
        self,
        max_suggestions: int = 10,
        entity_types: list[str] | None = None,
        debug_mode: bool = False,  # Add debug mode for troubleshooting
        max_concurrent_llm_calls: int = 4,  # Add concurrent LLM calls limit
    ) -> dict[str, Any]:
        """
        Generate node merge suggestions using LLM analysis.

        Args:
            max_suggestions: Maximum number of suggestions to return (default: 10)
            entity_types: Optional filter for specific entity types
            debug_mode: Enable debug mode with lower confidence threshold and verbose logging
            max_concurrent_llm_calls: Maximum concurrent LLM calls for batch analysis (default: 4)

        Returns:
            Dict containing merge suggestions and processing statistics

        Raises:
            Exception: If suggestion generation fails
        """
        import time

        from .operate import (
            analyze_entities_with_llm,
            filter_and_deduplicate_suggestions,
            filter_and_group_entities,
            get_high_degree_nodes,
        )
        from .types import MergeSuggestionsResult

        start_time = time.time()

        try:
            # Configuration constants
            MAX_ANALYZE_NODES = 500
            BATCH_SIZE = 100
            LLM_BATCH_SIZE = 50
            CONFIDENCE_THRESHOLD = 0.3 if debug_mode else 0.6  # Lower threshold in debug mode

            self.lightrag_logger.info(
                f"Starting merge suggestions generation: max_suggestions={max_suggestions}, "
                f"entity_types={entity_types}, debug_mode={debug_mode}, "
                f"confidence_threshold={CONFIDENCE_THRESHOLD}, "
                f"max_concurrent_llm_calls={max_concurrent_llm_calls}"
            )

            # Step 1: Get high-degree nodes from graph
            selected_nodes_dict, total_analyzed = await get_high_degree_nodes(
                self.chunk_entity_relation_graph,
                max_analyze_nodes=MAX_ANALYZE_NODES,
                batch_size=BATCH_SIZE,
                lightrag_logger=self.lightrag_logger,
            )

            if not selected_nodes_dict.labels:
                return MergeSuggestionsResult(
                    suggestions=[],
                    total_analyzed_nodes=0,
                    processing_time_seconds=time.time() - start_time,
                ).dict()

            # Step 2: Filter and group entities by type
            entities_by_type = await filter_and_group_entities(selected_nodes_dict, entity_types=entity_types)

            if not entities_by_type:
                return MergeSuggestionsResult(
                    suggestions=[],
                    total_analyzed_nodes=len(selected_nodes_dict.labels),
                    processing_time_seconds=time.time() - start_time,
                ).dict()

            # Step 3: Analyze entities with LLM (with early exit optimization and concurrency)
            suggestions = await analyze_entities_with_llm(
                entities_by_type,
                self.llm_model_func,
                confidence_threshold=CONFIDENCE_THRESHOLD,
                batch_size=LLM_BATCH_SIZE,
                max_suggestions=max_suggestions,  # Pass max_suggestions for early exit
                max_concurrent_llm_calls=max_concurrent_llm_calls,  # Pass concurrent limit
                tokenizer=self.tokenizer,
                llm_model_max_token_size=self.llm_model_max_token_size,
                summary_to_max_tokens=self.summary_to_max_tokens,
                lightrag_logger=self.lightrag_logger,
            )

            # Step 4: Final filtering (now mostly redundant due to early exit optimization)
            # Keep this for backward compatibility and final sorting by confidence
            final_suggestions = filter_and_deduplicate_suggestions(suggestions, max_suggestions)

            processing_time = time.time() - start_time
            total_analyzed_nodes = sum(len(entities) for entities in entities_by_type.values())

            # Convert to dict format for API response
            result = MergeSuggestionsResult(
                suggestions=final_suggestions,
                total_analyzed_nodes=total_analyzed_nodes,
                processing_time_seconds=processing_time,
            )

            self.lightrag_logger.info(
                f"Generated {len(final_suggestions)} merge suggestions using concurrent batch analysis "
                f"(processed {total_analyzed_nodes} entities in {processing_time:.2f}s with {max_concurrent_llm_calls} concurrent LLM calls)"
            )

            return result.dict()

        except Exception as e:
            self.lightrag_logger.error(f"Failed to generate merge suggestions: {str(e)}")
            raise e

    async def amerge_nodes(
        self,
        entity_ids: str | list[str],
        target_entity_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Merge multiple graph nodes into one, combining their descriptions, relationships, and vector data.

        This function merges multiple entities by:
        1. Determining target entity (auto-select by highest degree if not specified)
        2. Combining descriptions using default merge strategy
        3. Merging source_id, chunk_ids, and file_path information
        4. Updating all relationships to point to the target node
        5. Updating vector storage data
        6. Removing the source nodes

        Args:
            entity_ids: Single entity ID or list of entity IDs to merge
            target_entity_data: Optional target entity configuration including entity_name and other properties.
                              If not specified or empty, auto-select entity with highest degree

        Returns:
            Dict with merge results including target entity info

        Raises:
            ValueError: If entities don't exist or invalid parameters
        """
        # Ensure entity_ids is a list
        if isinstance(entity_ids, str):
            entity_ids = [entity_ids]

        if not entity_ids or len(entity_ids) < 1:
            raise ValueError("At least one entity ID must be provided")

        # If only one entity provided, return success (idempotent)
        if len(entity_ids) == 1:
            entity_id = entity_ids[0]
            self.lightrag_logger.info(f"Single entity provided, returning success: {entity_id}")

            # Get the entity data for response
            node_data = await self.chunk_entity_relation_graph.get_node(entity_id)
            if not node_data:
                raise ValueError(f"Entity '{entity_id}' does not exist")

            target_entity_response_data = {
                "entity_name": entity_id,
                "entity_type": node_data.get("entity_type", "UNKNOWN"),
                "description": node_data.get("description", ""),
                "source_id": node_data.get("source_id", ""),
                "file_path": node_data.get("file_path", ""),
            }

            return {
                "status": "success",
                "message": "Single entity provided, no merge needed",
                "target_entity_data": target_entity_response_data,
                "source_entities": [],
                "redirected_edges": 0,
                "merged_description_length": len(node_data.get("description", "")),
            }

        # Handle target_entity_data
        target_entity_data = {} if target_entity_data is None else target_entity_data.copy()

        # Extract target entity name
        target_entity_name = target_entity_data.get("entity_name")

        self.lightrag_logger.info(f"Starting multi-node merge: {entity_ids} -> {target_entity_name or 'auto-select'}")

        # Fixed merge strategy (no longer configurable)
        default_strategy = {
            "description": "concatenate",
            "entity_type": "keep_first",
            "source_id": "join_unique",
            "file_path": "join_unique",
        }

        # Get all entities and check they exist
        entities_data = {}
        for entity_id in entity_ids:
            node_data = await self.chunk_entity_relation_graph.get_node(entity_id)
            if not node_data:
                raise ValueError(f"Entity '{entity_id}' does not exist")
            entities_data[entity_id] = node_data

        # Determine target entity
        if target_entity_name is None:
            # Auto-select entity with highest degree (edge changes minimized)
            degrees = await self.chunk_entity_relation_graph.node_degrees_batch(entity_ids)
            target_entity_name = max(entity_ids, key=lambda x: degrees.get(x, 0))
            self.lightrag_logger.info(
                f"Auto-selected target entity: {target_entity_name} (degree: {degrees.get(target_entity_name, 0)})"
            )
        else:
            # Ensure target entity is in the list or exists
            if target_entity_name not in entity_ids:
                target_exists = await self.chunk_entity_relation_graph.has_node(target_entity_name)
                if target_exists:
                    # Target entity exists but not in merge list, add its data
                    target_data = await self.chunk_entity_relation_graph.get_node(target_entity_name)
                    entities_data[target_entity_name] = target_data
                    self.lightrag_logger.info(f"Target entity '{target_entity_name}' exists, merging into it")
                else:
                    self.lightrag_logger.info(f"Target entity '{target_entity_name}' will be created as new")

        # Determine source entities (all entities except target)
        source_entities = [eid for eid in entity_ids if eid != target_entity_name]

        # Merge entity data using default strategy
        merged_entity_data = self._merge_entity_attributes(list(entities_data.values()), default_strategy)

        # For entity_type, use the target entity's type if it exists, otherwise use the merged result
        if target_entity_name in entities_data:
            target_entity_type = entities_data[target_entity_name].get("entity_type")
            if target_entity_type:
                merged_entity_data["entity_type"] = target_entity_type

        # Apply target entity data overrides (from target_entity_data parameter)
        user_provided_description = None
        if target_entity_data:  # Only iterate if target_entity_data is not None
            for key, value in target_entity_data.items():
                if key != "entity_name":  # Don't override entity_name in the data
                    merged_entity_data[key] = value
                    if (
                        key == "description" and value is not None
                    ):  # Track if user provided description (including empty strings)
                        user_provided_description = value

        merged_entity_data["entity_id"] = target_entity_name

        # Only use auto-generated description if user didn't provide one
        if user_provided_description is None:
            # Calculate description info for LLM summary decision
            descriptions = [data.get("description", "") for data in entities_data.values() if data.get("description")]
            merged_description = GRAPH_FIELD_SEP.join(descriptions)

            # Skip LLM summarization to save cost and time
            # Previously we would call _handle_entity_relation_summary if num_fragments >= self.force_llm_summary_on_merge
            # Now we simply use the concatenated description as-is
            merged_entity_data["description"] = merged_description
        else:
            # Use user-provided description
            self.lightrag_logger.info(f"Using user-provided description for target entity {target_entity_name}")
            merged_entity_data["description"] = user_provided_description

        # Create/update target entity
        await self.chunk_entity_relation_graph.upsert_node(target_entity_name, merged_entity_data)
        self.lightrag_logger.debug(f"Updated target entity {target_entity_name} with merged data")

        # Process relationships
        all_relations = []
        relations_to_delete_vdb = []

        for entity_id in entity_ids:
            if entity_id == target_entity_name:
                continue  # Skip target entity to avoid self-processing

            source_edges = await self.chunk_entity_relation_graph.get_node_edges(entity_id)
            if source_edges:
                for src, tgt in source_edges:
                    edge_data = await self.chunk_entity_relation_graph.get_edge(src, tgt)
                    if edge_data:
                        all_relations.append((src, tgt, edge_data))
                        # Mark old relations for deletion from vector db
                        relations_to_delete_vdb.extend(
                            [
                                compute_mdhash_id(src + tgt, prefix="rel-", workspace=self.workspace),
                                compute_mdhash_id(tgt + src, prefix="rel-", workspace=self.workspace),
                            ]
                        )

        # Redirect relationships to target entity
        relation_updates = {}  # Track relationships that need to be merged
        redirected_edges = 0

        for src, tgt, edge_data in all_relations:
            new_src = target_entity_name if src in entity_ids else src
            new_tgt = target_entity_name if tgt in entity_ids else tgt

            # Skip self-loops
            if new_src == new_tgt:
                self.lightrag_logger.debug(f"Skipping self-loop edge: {src} -> {tgt}")
                continue

            # Check for duplicate relationships and merge them
            relation_key = tuple(sorted([new_src, new_tgt]))  # Undirected
            if relation_key in relation_updates:
                # Merge relationship data using default strategy
                existing_data = relation_updates[relation_key]["data"]
                merged_relation = self._merge_relation_attributes(
                    [existing_data, edge_data],
                    {
                        "description": "concatenate",
                        "keywords": "join_unique",
                        "source_id": "join_unique",
                        "file_path": "join_unique",
                        "weight": "max",
                    },
                )
                relation_updates[relation_key]["data"] = merged_relation
                self.lightrag_logger.debug(f"Merged duplicate relationship: {new_src} <-> {new_tgt}")
            else:
                relation_updates[relation_key] = {
                    "src": new_src,
                    "tgt": new_tgt,
                    "data": edge_data.copy(),
                }

            redirected_edges += 1

        # Apply relationship updates to graph
        for rel_data in relation_updates.values():
            await self.chunk_entity_relation_graph.upsert_edge(rel_data["src"], rel_data["tgt"], rel_data["data"])
            self.lightrag_logger.debug(f"Updated relationship: {rel_data['src']} <-> {rel_data['tgt']}")

        # Update vector storage for entities
        if self.entities_vdb:
            # Delete source entities from vector storage
            for entity_id in source_entities:
                await self.entities_vdb.delete_entity(entity_id)
                self.lightrag_logger.debug(f"Deleted source entity {entity_id} from vector storage")

            # Update target entity in vector storage
            entity_content = f"{target_entity_name}\n{merged_entity_data.get('description', '')}"
            entity_id = compute_mdhash_id(target_entity_name, prefix="ent-", workspace=self.workspace)

            entity_vdb_data = {
                entity_id: {
                    "entity_name": target_entity_name,
                    "entity_type": merged_entity_data.get("entity_type", "UNKNOWN"),
                    "content": entity_content,
                    "source_id": merged_entity_data.get("source_id", ""),
                    "file_path": merged_entity_data.get("file_path", ""),
                }
            }
            await self.entities_vdb.upsert(entity_vdb_data)
            self.lightrag_logger.debug(f"Updated target entity {target_entity_name} in vector storage")

        # Update vector storage for relationships
        if self.relationships_vdb:
            # Delete old relationship records
            if relations_to_delete_vdb:
                await self.relationships_vdb.delete(relations_to_delete_vdb)
                self.lightrag_logger.debug(
                    f"Deleted {len(relations_to_delete_vdb)} old relationship records from vector storage"
                )

            # Create new relationship records
            new_rel_data = {}
            for rel_data in relation_updates.values():
                src, tgt = rel_data["src"], rel_data["tgt"]
                edge_data = rel_data["data"]

                rel_content = f"{src}\t{tgt}\n{edge_data.get('keywords', '')}\n{edge_data.get('description', '')}"
                rel_id = compute_mdhash_id(src + tgt, prefix="rel-", workspace=self.workspace)

                new_rel_data[rel_id] = {
                    "src_id": src,
                    "tgt_id": tgt,
                    "content": rel_content,
                    "source_id": edge_data.get("source_id", ""),
                    "file_path": edge_data.get("file_path", ""),
                    "keywords": edge_data.get("keywords", ""),
                    "description": edge_data.get("description", ""),
                    "weight": edge_data.get("weight", 1.0),
                }

            if new_rel_data:
                await self.relationships_vdb.upsert(new_rel_data)
                self.lightrag_logger.debug(f"Updated {len(new_rel_data)} relationship records in vector storage")

        # Delete source entities from graph storage
        for entity_id in source_entities:
            await self.chunk_entity_relation_graph.delete_node(entity_id)
            self.lightrag_logger.debug(f"Deleted source entity {entity_id} from graph storage")

        self.lightrag_logger.info(
            f"Multi-node merge completed: {source_entities} -> {target_entity_name}, redirected {redirected_edges} edges"
        )

        # Prepare complete target entity data for response
        target_entity_response_data = {
            "entity_name": target_entity_name,
            "entity_type": merged_entity_data.get("entity_type", "UNKNOWN"),
            "description": merged_entity_data.get("description", ""),
            "source_id": merged_entity_data.get("source_id", ""),
            "file_path": merged_entity_data.get("file_path", ""),
        }

        return {
            "status": "success",
            "message": f"Successfully merged {len(source_entities)} entities into {target_entity_name}",
            "target_entity_data": target_entity_response_data,
            "source_entities": source_entities,
            "redirected_edges": redirected_edges,
            "merged_description_length": len(merged_entity_data.get("description", "")),
        }

    def _merge_entity_attributes(
        self, entity_data_list: list[dict[str, Any]], merge_strategy: dict[str, str]
    ) -> dict[str, Any]:
        """Merge attributes from multiple entities using specified strategy."""
        merged_data = {}

        # Collect all possible keys
        all_keys = set()
        for data in entity_data_list:
            all_keys.update(data.keys())

        # Merge values for each key
        for key in all_keys:
            # Get all non-empty values for this key
            values = [data.get(key) for data in entity_data_list if data.get(key)]

            if not values:
                continue

            # Apply merge strategy
            strategy = merge_strategy.get(key, "keep_first")

            if strategy == "concatenate":
                merged_data[key] = GRAPH_FIELD_SEP.join(str(v) for v in values)
            elif strategy == "keep_first":
                merged_data[key] = values[0]
            elif strategy == "keep_last":
                merged_data[key] = values[-1]
            elif strategy == "join_unique":
                # Handle fields separated by GRAPH_FIELD_SEP
                unique_items = set()
                for value in values:
                    if value:
                        items = str(value).split(GRAPH_FIELD_SEP)
                        unique_items.update(item.strip() for item in items if item.strip())
                merged_data[key] = GRAPH_FIELD_SEP.join(sorted(unique_items))
            else:
                # Default: keep first
                merged_data[key] = values[0]

        return merged_data

    def _merge_relation_attributes(
        self, relation_data_list: list[dict[str, Any]], merge_strategy: dict[str, str]
    ) -> dict[str, Any]:
        """Merge attributes from multiple relationships using specified strategy."""
        merged_data = {}

        # Collect all possible keys
        all_keys = set()
        for data in relation_data_list:
            all_keys.update(data.keys())

        # Merge values for each key
        for key in all_keys:
            # Get all non-None values for this key
            values = [data.get(key) for data in relation_data_list if data.get(key) is not None]

            if not values:
                continue

            # Apply merge strategy
            strategy = merge_strategy.get(key, "keep_first")

            if strategy == "concatenate":
                merged_data[key] = GRAPH_FIELD_SEP.join(str(v) for v in values)
            elif strategy == "keep_first":
                merged_data[key] = values[0]
            elif strategy == "keep_last":
                merged_data[key] = values[-1]
            elif strategy == "join_unique":
                # Handle fields separated by GRAPH_FIELD_SEP or commas
                unique_items = set()
                for value in values:
                    if value:
                        # Try both separators
                        items = str(value).replace(",", GRAPH_FIELD_SEP).split(GRAPH_FIELD_SEP)
                        unique_items.update(item.strip() for item in items if item.strip())
                merged_data[key] = (
                    ",".join(sorted(unique_items)) if key == "keywords" else GRAPH_FIELD_SEP.join(sorted(unique_items))
                )
            elif strategy == "max":
                # For numeric fields like weight
                try:
                    merged_data[key] = max(float(v) for v in values)
                except (ValueError, TypeError):
                    merged_data[key] = values[0]
            else:
                # Default: keep first
                merged_data[key] = values[0]

        return merged_data

    async def export_for_kg_eval(
        self,
        sample_size: int = 100000,
        include_source_texts: bool = True,
    ) -> dict[str, Any]:
        """
        Export workspace data in KG-Eval framework format for knowledge graph evaluation.

        This method extracts entities, relationships, and source texts from the current workspace
        and formats them according to the KG-Eval evaluation framework structure.

        Args:
            sample_size: Number of entities to sample (default: 100000)
            include_source_texts: Whether to include source texts in the output (default: True)

        Returns:
            Dictionary containing entities, relationships, and optionally source_texts
            in KG-Eval format, compatible with sample_kg_mini.json structure
        """
        try:
            self.lightrag_logger.info(f"Starting KG-Eval export for workspace {self.workspace}")

            # Get all node labels (entity names) - single call
            all_labels = await self.chunk_entity_relation_graph.get_all_labels()
            self.lightrag_logger.debug(f"Found {len(all_labels)} entities in workspace {self.workspace}")

            # Sample nodes for export (take first N)
            sampled_labels = all_labels[:sample_size] if len(all_labels) > sample_size else all_labels
            self.lightrag_logger.debug(f"Sampling {len(sampled_labels)} entities for export")

            # Early return if no entities
            if not sampled_labels:
                return {"entities": [], "relationships": [], "source_texts": []}

            # Batch get all node data and edges in parallel
            nodes_data_task = self.chunk_entity_relation_graph.get_nodes_batch(sampled_labels)
            nodes_edges_task = self.chunk_entity_relation_graph.get_nodes_edges_batch(sampled_labels)

            # Execute both tasks concurrently
            nodes_data, nodes_edges = await asyncio.gather(nodes_data_task, nodes_edges_task)

            # Prepare entities list in KG-Eval format (direct iteration, no redundant operations)
            entities = [
                {
                    "entity_name": node_data.get("entity_name", entity_id),
                    "entity_type": node_data.get("entity_type"),
                    "description": node_data.get("description"),
                }
                for entity_id, node_data in nodes_data.items()
            ]

            # Collect edge pairs that connect our sampled nodes (optimized filtering)
            sampled_labels_set = set(sampled_labels)  # O(1) lookup
            edge_pairs_to_query = {
                (source_entity_id, target_entity_id)
                for edges in nodes_edges.values()
                for source_entity_id, target_entity_id in edges
                if source_entity_id in sampled_labels_set and target_entity_id in sampled_labels_set
            }

            self.lightrag_logger.debug(f"Found {len(edge_pairs_to_query)} edges between sampled entities")

            # Batch get edge details (single call)
            relationships = []
            edges_data = {}
            if edge_pairs_to_query:
                edge_pairs_list = [{"src": src, "tgt": tgt} for src, tgt in edge_pairs_to_query]
                edges_data = await self.chunk_entity_relation_graph.get_edges_batch(edge_pairs_list)

                # Process relationships efficiently
                relationships = [
                    {
                        "source_entity_name": nodes_data.get(source_entity_id, {}).get("entity_name", source_entity_id),
                        "target_entity_name": nodes_data.get(target_entity_id, {}).get("entity_name", target_entity_id),
                        "description": edge_data.get("description", ""),
                        "keywords": [kw.strip() for kw in edge_data.get("keywords", "").split(",") if kw.strip()],
                        "weight": float(edge_data.get("weight", 0.0)),
                    }
                    for (source_entity_id, target_entity_id), edge_data in edges_data.items()
                ]

            # Initialize result
            result = {
                "entities": entities,
                "relationships": relationships,
            }

            # Get source texts by tracing back from entities/edges to chunks (if requested)
            if include_source_texts:
                self.lightrag_logger.debug("Extracting source texts...")

                # Collect all chunk IDs efficiently (single pass through data)
                chunk_id_to_entities = {}
                chunk_id_to_edges = {}

                # Process entities source_ids
                for entity_id, node_data in nodes_data.items():
                    source_id = node_data.get("source_id")
                    if source_id:
                        chunk_ids = source_id.split(GRAPH_FIELD_SEP) if GRAPH_FIELD_SEP in source_id else [source_id]
                        entity_name = node_data.get("entity_name", entity_id)
                        for chunk_id in chunk_ids:
                            chunk_id = chunk_id.strip()
                            if chunk_id:
                                chunk_id_to_entities.setdefault(chunk_id, []).append(entity_name)

                # Process edges source_ids
                for (source_entity_id, target_entity_id), edge_data in edges_data.items():
                    source_id = edge_data.get("source_id")
                    if source_id:
                        chunk_ids = source_id.split(GRAPH_FIELD_SEP) if GRAPH_FIELD_SEP in source_id else [source_id]
                        source_name = nodes_data.get(source_entity_id, {}).get("entity_name", source_entity_id)
                        target_name = nodes_data.get(target_entity_id, {}).get("entity_name", target_entity_id)
                        edge_tuple = [source_name, target_name]

                        for chunk_id in chunk_ids:
                            chunk_id = chunk_id.strip()
                            if chunk_id:
                                chunk_id_to_edges.setdefault(chunk_id, []).append(edge_tuple)

                # Get unique chunk IDs that have linked entities or edges
                linked_chunk_ids = set(chunk_id_to_entities.keys()) | set(chunk_id_to_edges.keys())
                self.lightrag_logger.debug(f"Found {len(linked_chunk_ids)} linked chunks")

                # Batch get chunk contents (single call)
                source_texts = []
                if linked_chunk_ids:
                    chunk_contents = await self.chunks_vdb.get_by_ids(list(linked_chunk_ids))

                    # Process source texts efficiently (single pass)
                    source_texts = [
                        {
                            "content": chunk_data.get("content", ""),
                            "linked_entity_names": chunk_id_to_entities.get(chunk_data.get("id"), []),
                            "linked_edges": chunk_id_to_edges.get(chunk_data.get("id"), []),
                        }
                        for chunk_data in chunk_contents
                        if chunk_data.get("id")
                    ]

                result["source_texts"] = source_texts

            # Log summary
            summary_msg = f"KG-Eval export completed: {len(entities)} entities, {len(relationships)} relationships"
            if include_source_texts:
                summary_msg += f", {len(result.get('source_texts', []))} source texts"
            self.lightrag_logger.info(summary_msg)

            return result

        except Exception as e:
            self.lightrag_logger.error(f"KG-Eval export failed: {str(e)}")
            raise e
