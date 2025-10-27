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

import asyncio
import logging
import uuid
from collections import deque
from typing import Any, AsyncGenerator, Dict, List, Set

from jinja2 import Environment, StrictUndefined

import aperag.flow.runners  # noqa: F401
from aperag.flow.base.exceptions import CycleError, ValidationError
from aperag.flow.base.models import NODE_RUNNER_REGISTRY, ExecutionContext, FlowInstance, NodeInstance, SystemInput
from aperag.utils.utils import utc_now

# Configure logging
logger = logging.getLogger(__name__)


class FlowEvent:
    """Event emitted during flow execution"""

    def __init__(self, event_type: str, node_id: str, node_type: str, execution_id: str, data: Dict[str, Any] = None):
        self.event_type = event_type
        self.node_id = node_id
        self.node_type = node_type
        self.execution_id = execution_id
        self.timestamp = utc_now().isoformat()
        self.data = data or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "node_id": self.node_id,
            "node_type": self.node_type or "",
            "execution_id": self.execution_id,
            "timestamp": self.timestamp,
            "data": self.data,
        }


class FlowEventType:
    """Event types for flow execution"""

    NODE_START = "node_start"
    NODE_END = "node_end"
    NODE_ERROR = "node_error"
    FLOW_START = "flow_start"
    FLOW_END = "flow_end"
    FLOW_ERROR = "flow_error"


# FlowEngine is responsible for executing a FlowInstance (a flow definition with nodes and edges).
# Each FlowEngine instance maintains its own execution context (self.context) and execution_id.
# Usage notes:
# - Do NOT reuse the same FlowEngine instance for multiple or concurrent flow executions.
#   Each execution should use a new FlowEngine instance to avoid context and execution_id conflicts.
# - The context stores all global variables and node outputs for the current execution.
# - The execution_id is a unique identifier for the current execution, mainly for logging and tracing.
# - Reusing the same FlowEngine instance for multiple executions will result in data corruption or unexpected behavior.
class FlowEngine:
    """Engine for executing flow instances"""

    def __init__(self):
        self.context = ExecutionContext()
        self.execution_id = None
        self._event_queue = asyncio.Queue()
        self.jinja_env = Environment(undefined=StrictUndefined)

    async def emit_event(self, event: FlowEvent):  # 事件驱动。通过 emit_event 方法在节点开始（NODE_START）、结束（NODE_END）、出错（NODE_ERROR）时发送事件，便于监控流程执行状态（如日志记录、前端展示）。
        """Emit an event to all consumers"""
        await self._event_queue.put(event)
        # Also log the event
        logger.info(
            f"Flow event: {event.event_type} for {event.node_type} node {event.node_id}",
            extra={"execution_id": self.execution_id},
        )

    async def get_events(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Get events as an async generator"""
        try:
            while True:
                event = await self._event_queue.get()
                yield event.to_dict()
                self._event_queue.task_done()
        except asyncio.CancelledError:
            pass

    async def execute_flow(self, flow: FlowInstance, initial_data: Dict[str, Any] = None) -> Dict[str, Any]:  # 执行流程
        """Execute a flow instance with optional initial data

        Args:
            flow: The flow instance to execute
            initial_data: Optional dictionary of initial global variable values

        Returns:
            Dictionary of final output values from the flow execution
        """
        # Generate execution ID
        self.execution_id = str(uuid.uuid4())[:8]  # Use first 8 characters of UUID
        logger.info(
            f"Starting flow execution {self.execution_id} for flow {flow.name}",
            extra={"execution_id": self.execution_id},
        )

        try:
            # Emit flow start event
            await self.emit_event(
                FlowEvent(
                    event_type=FlowEventType.FLOW_START,
                    execution_id=self.execution_id,
                    node_id=None,
                    node_type=None,
                    data={"flow_name": flow.name},
                )
            )  # 发起流程开始事件

            # Initialize global variables
            if initial_data:
                for var_name, var_value in initial_data.items():
                    self.context.set_global(var_name, var_value)

            # Build dependency graph and perform topological sort
            sorted_nodes = self._topological_sort(flow)  # 对流程实例进行拓扑排序【检测流程图是否含有循环结构，有则触发异常】

            """
            以单个知识库的混合检索流程为例，并行组依次为：
            [向量检索节点、全文检索节点、图谱检索节点、摘要检索节点、视觉信息检索节点]
            [合并节点]
            [重排节点]
            """
            # Execute nodes
            for node_group in self._find_parallel_groups(flow, sorted_nodes):  # 查找可以并行执行的节点组（逐级执行），采用协程异步方式结合await实现“组内并行执行，组间串行等待”
                await self._execute_node_group(flow, node_group)  # 阻塞当前循环，等待当前组内所有节点并行执行完毕后，再进入下一次迭代（执行下一组）

            # Emit flow end event
            await self.emit_event(
                FlowEvent(
                    event_type=FlowEventType.FLOW_END,
                    execution_id=self.execution_id,
                    node_id=None,
                    node_type=None,
                    data={"flow_name": flow.name},
                )
            )  # 发起流程结束事件

            logger.info(f"Completed flow execution {self.execution_id}", extra={"execution_id": self.execution_id})
            return self.context.outputs, self.context.system_outputs

        except Exception as e:
            # Emit flow error event
            await self.emit_event(
                FlowEvent(
                    event_type=FlowEventType.FLOW_ERROR,
                    execution_id=self.execution_id,
                    node_id=None,
                    node_type=None,
                    data={"flow_name": flow.name, "error": str(e)},
                )
            )
            raise e

    def _topological_sort(self, flow: FlowInstance) -> List[str]:  # 对流程实例进行拓扑排序，得到排序后的节点【执行拓扑排序检测循环】
        """Perform topological sort to detect cycles

        Args:
            flow: The flow instance

        Returns:
            Topologically sorted list of node IDs

        Raises:
            CycleError: If the flow contains cycles
        """
        """
        单个知识库的混合检索流程：
        第一阶段：并行检索节点【各节点入度皆为0】
        
            向量检索节点、全文检索节点、图谱检索节点、摘要检索节点、视觉信息检索节点
        
        第二阶段：合并节点【入度为5】
        
            向量检索节点、全文检索节点、图谱检索节点、摘要检索节点、视觉信息检索节点 全部完成后，共同进入合并节点
        
        第三阶段：重排节点【入度为1】
        
            合并节点 完成后，进入重排节点，流程结束
        """
        # Build dependency graph from edges
        in_degree = {node_id: 0 for node_id in flow.nodes}  # 初始化各节点入度为0
        for edge in flow.edges:  # 提取各节点入度
            in_degree[edge.target] += 1

        # Start with nodes that have no dependencies
        queue = deque([node_id for node_id, degree in in_degree.items() if degree == 0])  # 收集入度为0的节点，形成节点列表，构建队列
        if len(queue) == 0:  # 如果所有节点入度非0，则说明流程存在循环【抛出异常】
            raise CycleError("Flow contains cycles")

        sorted_nodes = []

        while queue:  # 遍历入度为0的节点
            node_id = queue.popleft()
            sorted_nodes.append(node_id)

            # Update in-degree of successor nodes
            for edge in flow.edges:
                if edge.source == node_id:  # 处理以当前节点为起点的终点节点
                    in_degree[edge.target] -= 1  # 终点节点入度减1更新
                    if in_degree[edge.target] == 0:  # 将新的入度为0的节点，从右侧插入队列
                        queue.append(edge.target)
        """
        以单个知识库的混合检索流程为例，最终得到sorted_nodes：
        [向量检索节点、全文检索节点、图谱检索节点、摘要检索节点、视觉信息检索节点、合并节点、重排节点【可选】]
            说明1：前5个检索节点的顺序可随机排布，并无固定的先后顺序。
            说明2：拓扑排序的直观理解是按照流程图的先后顺序进行排序的
        """
        if len(sorted_nodes) != len(flow.nodes):
            raise CycleError("Flow contains cycles")

        return sorted_nodes

    def _find_parallel_groups(self, flow: FlowInstance, sorted_nodes: List[str]) -> List[Set[str]]:  # 查找可以并行执行的节点组（逐级执行）
        """Find groups of nodes that can be executed in parallel (level by level)

        Args:
            flow: The flow instance
            sorted_nodes: Topologically sorted list of node IDs

        Returns:
            List of node groups, where each group can be executed in parallel
        """
        # Build in-degree map
        in_degree = {node_id: 0 for node_id in flow.nodes}  # 初始化各节点入度为0
        for edge in flow.edges:  # 提取各节点入度
            in_degree[edge.target] += 1

        # Track processed nodes
        processed = set()
        groups = []

        while len(processed) < len(sorted_nodes):  # 存在未处理节点
            # Find all nodes with in-degree 0 and not processed
            current_group = set(
                node_id for node_id in sorted_nodes if in_degree[node_id] == 0 and node_id not in processed
            )  # 将当前入度为0且未处理的节点归为一组
            if not current_group:
                break  # Should not happen if topological sort is correct
            groups.append(current_group)  # 收集当前组
            # Mark nodes as processed and update in-degree for successors
            # 其实这里和拓扑排序的逻辑一样，可以理解为“按照不同批次入度为0的规则进行分组，每一组的节点是同一批次入度为0的节点集合，可并行执行”
            for node_id in current_group:  # 对于当前组中的节点，将其放入已处理节点集合，并对以其为起点的终点节点做入度减1操作
                processed.add(node_id)
                for edge in flow.edges:
                    if edge.source == node_id:
                        in_degree[edge.target] -= 1
        return groups

    async def _execute_node_group(self, flow: FlowInstance, node_group: Set[str]):
        """Execute a group of nodes (possibly in parallel)"""
        logger.info(f"Executing node group: {node_group}", extra={"execution_id": self.execution_id})
        if len(node_group) == 1:
            node_id = next(iter(node_group))
            node = flow.nodes[node_id]
            await self._execute_node(node)
        else:  # 并行节点组内含有多个节点
            tasks = []
            for node_id in node_group:
                node = flow.nodes[node_id]
                tasks.append(self._execute_node(node))
            """
            asyncio.gather 是 Python 异步编程中用于并发执行多个协程并收集结果的核心函数，
            其底层实现依赖于 asyncio 事件循环（Event Loop）的调度机制，
            核心原理可以概括为：“统一管理多个协程的生命周期，通过事件循环调度它们并发执行，并在所有协程完成后聚合结果”。
            """
            await asyncio.gather(*tasks)  # 使用gather并发执行多个协程任务并收集结果

    def _resolve_variable(self, expr: str, nodes_ctx: dict):
        """
        Resolve variable path like 'nodes.start.output.query' from nodes_ctx.
        """
        parts = expr.strip().split(".")
        if not parts:
            return None
        if parts[0] == "nodes":
            if len(parts) < 4 or parts[2] != "output":
                raise ValidationError(f"Invalid variable reference: ${{{{ {expr} }}}}")
            node_id = parts[1]
            field_path = parts[3:]
            node_outputs = self.context.outputs.get(node_id, {})
            value = node_outputs
            for key in field_path:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                elif isinstance(value, object) and hasattr(value, key):
                    value = getattr(value, key)
                else:
                    raise ValidationError(f"Cannot resolve variable: ${{{{ {expr} }}}}")
            return value
        else:
            raise ValidationError(f"Unknown variable scope: ${{{{ {expr} }}}}")

    def resolve_expression(self, value, node_id=None, nodes_ctx=None):
        """
        Recursively resolve input values.
        1. If value is a string and starts with ${{ ... }}, resolve as variable path.
        2. Otherwise, use jinja2 template rendering with nodes_ctx as context.
        3. Recursively handle dict/list.
        """
        if nodes_ctx is None:
            nodes_ctx = {nid: {"output": outputs} for nid, outputs in self.context.outputs.items()}
        if isinstance(value, dict):
            return {k: self.resolve_expression(v, node_id, nodes_ctx) for k, v in value.items()}
        if isinstance(value, list):
            return [self.resolve_expression(v, node_id, nodes_ctx) for v in value]
        if not isinstance(value, str):
            return value

        value_strip = value.strip()
        # Only handle variable reference like {{ ... }}
        # This is a workaround for the fact that the rendered output of jinja2 is a string, but we want to get the original value of the variable
        if value_strip.startswith("{{") and value_strip.endswith("}}"):
            expr = value_strip[2:-2].strip()
            return self._resolve_variable(expr, nodes_ctx)

        # Otherwise, use jinja2 template rendering
        try:
            template = self.jinja_env.from_string(value)
            rendered = template.render(nodes=nodes_ctx)
        except Exception as e:
            raise ValidationError(f"Jinja2 render error in node '{node_id}': {e}")
        return rendered

    def convert_type_by_schema(self, value, field_schema):
        """Convert value to the type declared in field_schema (jsonschema property)."""
        if value is None:
            return None
        typ = field_schema.get("type")
        if typ == "string":
            return str(value)
        if typ == "integer":
            try:
                return int(value)
            except Exception:
                raise ValueError(f"Cannot convert '{value}' to integer")
        if typ == "number":
            try:
                return float(value)
            except Exception:
                raise ValueError(f"Cannot convert '{value}' to float")
        if typ == "boolean":
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                if value.lower() in ["true", "1", "yes"]:
                    return True
                if value.lower() in ["false", "0", "no"]:
                    return False
            if isinstance(value, int):
                return bool(value)
            raise ValueError(f"Cannot convert '{value}' to boolean")
        if typ == "array":
            if isinstance(value, list):
                return value
            if isinstance(value, str):
                import json

                try:
                    arr = json.loads(value)
                    if isinstance(arr, list):
                        return arr
                except Exception as e:
                    raise ValidationError(f"Cannot convert '{value}' to array: {e}")
                # Try comma split
                return [v.strip() for v in value.split(",") if v.strip()]
            raise ValueError(f"Cannot convert '{value}' to array")
        if typ == "object":
            if isinstance(value, dict):
                return value
            if isinstance(value, str):
                import json

                try:
                    obj = json.loads(value)
                    if isinstance(obj, dict):
                        return obj
                except Exception:
                    pass
            raise ValueError(f"Cannot convert '{value}' to object")
        return value

    def _bind_node_inputs(self, node: NodeInstance, runner_info: dict) -> tuple:
        """
        Bind input variables for a node using Pydantic model from runner_info.
        Returns (user_input, sys_input)
        """
        raw_inputs = getattr(node, "input_values", {})
        resolved_inputs = self.resolve_expression(raw_inputs, node.id)
        input_model = runner_info["input_model"]
        try:
            user_input = input_model.model_validate(resolved_inputs)
        except Exception as e:
            raise ValidationError(f"Input validation error for node {node.id}: {e}")
        sys_input = SystemInput(**self.context.global_variables)
        return user_input, sys_input

    async def _execute_node(self, node: NodeInstance) -> None:  # 执行流程图中的单个节点
        """
        Execute a single node using the provided context, using runner_info from registry.
        """
        runner_info = NODE_RUNNER_REGISTRY.get(node.type)  # 从节点仓库依据节点类型获取节点运行信息【详情见aperag.flow.base.models.register_node_runner中对于节点运行信息的注册定义】
        if not runner_info:
            raise ValidationError(f"Unknown node type: {node.type}")
        runner = runner_info["runner"]  # 节点运行实例
        try:
            user_input, sys_input = self._bind_node_inputs(node, runner_info)  # 构造节点输入数据
            await self.emit_event(
                FlowEvent(
                    FlowEventType.NODE_START,
                    node.id,
                    node.type,
                    self.execution_id,
                    {"node_type": node.type, "inputs": user_input.model_dump()},
                )
            )
            outputs = await runner.run(user_input, sys_input)  # 运行节点【执行具体节点定义类的run方法】，获取节点运行输出数据
            if isinstance(outputs, tuple) and len(outputs) == 2:
                output_data, system_output = outputs
            else:
                output_data, system_output = outputs, None
            # TODO 关键步骤：将节点运行结果放入self.context中
            self.context.set_output(node.id, output_data)
            if system_output is not None:
                self.context.set_system_output(node.id, system_output)

            await self.emit_event(
                FlowEvent(
                    FlowEventType.NODE_END,
                    node.id,
                    node.type,
                    self.execution_id,
                    {"node_type": node.type, "outputs": output_data},
                )
            )
        except Exception as e:
            await self.emit_event(
                FlowEvent(
                    FlowEventType.NODE_ERROR,
                    node.id,
                    node.type,
                    self.execution_id,
                    {"node_type": node.type, "error": str(e)},
                )
            )
            raise e

    def update_node_input(self, flow: FlowInstance, node_id: str, value: Any):
        """Update the input values for a node"""
        flow.nodes[node_id].input_values.update(value)

    def find_start_nodes(self, flow: FlowInstance) -> str:
        """Find all start nodes (nodes with in-degree == 0) in the flow"""
        in_degree = {node_id: 0 for node_id in flow.nodes}
        for edge in flow.edges:
            in_degree[edge.target] += 1
        start_nodes = [node_id for node_id in flow.nodes if in_degree[node_id] == 0]
        if len(start_nodes) != 1:
            raise ValidationError("Flow must have exactly one start node")
        return start_nodes[0]

    def find_end_nodes(self, flow: FlowInstance) -> List[str]:
        """Find all output nodes (nodes with in-degree > 0 and out-degree 0) in the flow"""
        out_degree = {node_id: 0 for node_id in flow.nodes}
        for edge in flow.edges:
            out_degree[edge.source] += 1
        output_nodes = [node_id for node_id in flow.nodes if out_degree[node_id] == 0]
        return output_nodes
