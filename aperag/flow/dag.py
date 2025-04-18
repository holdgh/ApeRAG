import json
import yaml
import padantic

from typing import List, Callable, Dict, Any, Tuple, Union
from enum import Enum

class NodeType(Enum):
    START = "start"
    VECTOR_RETRIEVE = "vector_retrieve"
    KEYWORD_RETRIEVE = "keyword_retrieve"
    RERANK = "rerank"
    LLM_CHAT = "llm_chat"
    END = "end"

class Node:
    """
    A node in the DAG
    """
    def __init__(self, id: str, type: NodeType, vars: Dict[str, Any]):
        self.id = id
        self.type = type
        self.vars = vars

    def __eq__(self, other):
        if not isinstance(other, Node):
            return False
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)


class Edge:
    """
    An edge in the DAG
    """
    def __init__(self, source: Node, target: Node):
        self.source = source
        self.target = target

    def __eq__(self, other):
        if not isinstance(other, Edge):
            return False
        return self.source == other.source and self.target == other.target

    def __hash__(self):
        return hash((self.source, self.target))


class DAG:
    def __init__(self):
        """
        Initialize the DAG
        """
        self.nodes: dict[Node, Node] = {}
        self.edges: dict[Edge, Edge] = {}

    def add_node(self, node: Node) -> bool:
        """
        Add a node to the DAG
        Returns:
            bool: True if added, False otherwise
        """
        if not node:
            return False
        self.nodes[node] = node
        return True
    
    def add_edge(self, edge: Edge) -> bool:
        """
        Add an edge to the DAG
        Returns:
            bool: True if added, False otherwise
        """
        if edge in self.edges:
            return False
        self.edges[edge] = edge
        return True
    
    def remove_node(self, node: Node) -> bool:
        """
        Remove a node from the DAG
        Returns:
            bool: True if removed, False otherwise
        """
        if node not in self.nodes:
            return False
        del self.nodes[node]
        for edge in self.edges.values():
            if edge.source == node or edge.target == node:
                del self.edges[edge]
        return True

    def remove_edge(self, edge: Edge) -> bool:
        """
        Remove an edge from the DAG
        Returns:
            bool: True if removed, False otherwise
        """
        if edge not in self.edges:
            return False
        del self.edges[edge]
        return True
    
    def connect_root_to(self, node: Node) -> bool:
        """
        Connect the root node to the given node
        Returns:
            bool: True if connected, False otherwise
        """
        if node in self.nodes:
            return False
        edge = Edge(self.root(), node)
        self.edges[edge] = edge
        return True
    
    def connect(self, source: Node, target: Node) -> bool:
        """
        Connect two nodes
        Returns:
            bool: True if connected, False otherwise
        """
        if source == target:
            return False
        if not source or not target:
            return False
        if edge in self.edges:
            return False
        if not self.add_node(target):
            return False
        edge = Edge(source, target)
        self.edges[edge] = edge
        return True
    
    def root(self) -> Node:
        """
        Get the root node of the DAG
        Returns:
            Node: Root node of the DAG
        """
        roots = []
        for node in self.nodes.values():
            if len(self.in_adjacent(node)) == 0:
                roots.append(node)
        if len(roots) == 0:
            raise ValueError("No root node found")
        if len(roots) > 1:
            raise ValueError("Multiple root nodes found")
        return roots[0]
    
    def end(self) -> Node:
        """
        Get the end node of the DAG
        Returns:
            Node: End node of the DAG
        """
        ends = []
        for node in self.nodes.values():
            if len(self.out_adjacent(node)) == 0:
                ends.append(node)
        if len(ends) == 0:
            raise ValueError("No end node found")
        if len(ends) > 1:
            raise ValueError("Multiple end nodes found")
        return ends[0]
    
    def in_adjacent(self, node: Node) -> List[Node]:
        """
        Get the nodes that have an edge to the given node
        Returns:
            List[Node]: List of nodes that have an edge to the given node
        """
        return [edge.source for edge in self.edges.values() if edge.target == node]
    
    def out_adjacent(self, node: Node) -> List[Node]:
        """
        Get the nodes that have an edge from the given node
        Returns:
            List[Node]: List of nodes that have an edge from the given node
        """
        return [edge.target for edge in self.edges.values() if edge.source == node]

    def validate(self) -> bool:
        """
        Validate if the DAG structure is valid
        Returns:
            bool: True if valid, False otherwise
        """
        # Check if DAG is empty
        if not self.nodes:
            return False

        start_node = self.root()
        end_node = self.end()
        
        # Check for cycles using DFS
        def has_cycle(node: Node, visited: set, recursion_stack: set) -> bool:
            visited.add(node)
            recursion_stack.add(node)
            
            for neighbor in self.out_adjacent(node):
                if neighbor not in visited:
                    if has_cycle(neighbor, visited, recursion_stack):
                        return True
                elif neighbor in recursion_stack:
                    return True
            
            recursion_stack.remove(node)
            return False

        visited = set()
        recursion_stack = set()
        if has_cycle(start_node, visited, recursion_stack):
            return False

        # Check if all nodes are reachable from start
        def dfs(node: Node, visited: set):
            visited.add(node)
            for neighbor in self.out_adjacent(node):
                if neighbor not in visited:
                    dfs(neighbor, visited)

        visited = set()
        dfs(start_node, visited)
        if len(visited) != len(self.nodes):
            return False

        # Check if end node is reachable from all nodes
        def can_reach_end(node: Node, visited: set) -> bool:
            if node == end_node:
                return True
            if node in visited:
                return False
            visited.add(node)
            for neighbor in self.out_adjacent(node):
                if can_reach_end(neighbor, visited):
                    return True
            return False

        for node in self.nodes.values():
            if not can_reach_end(node, set()):
                return False

        return True

    def walk(self, global_ctxs: Dict[Node, Dict[str, Any]], f: Callable[[Node, Dict[Node, Dict[str, Any]], Dict[Node, Dict[str, Any]]], Tuple[Dict[str, Any], bool]]) -> List[Node]:
        """
        Walk the DAG and apply the function to each node
        Returns:
            List[Node]: List of nodes visited
        """
        if not self.validate():
            raise ValueError("Invalid DAG")

        visited = set()
        queue = [self.root()]
        while queue:
            node = queue.pop(0)
            if node in visited:
                continue
            input_ctxs = {}
            for adjacent in self.in_adjacent(node):
                input_ctxs[adjacent] = global_ctxs.get(adjacent, {})
            ctxs, is_continue = f(node, input_ctxs)
            global_ctxs[node] = ctxs
            visited.add(node)
            if is_continue:
                queue.extend(self.out_adjacent(node))
            else:
                break
        return list(visited)

def parse_dag(data: Union[str, Dict[str, Any]]) -> DAG:
    """
    Build DAG from JSON data
    Args:
        data: JSON string or dict containing nodes and edges
    Returns:
        DAG object
    """
    # Parse JSON if input is string
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            data = yaml.safe_load(data)
    
    dag = DAG()
    node_map = {}  # Map node id to Node object
    
    # Create nodes
    for node_data in data["nodes"]:
        node_id = node_data["id"]
        node_type = NodeType(node_data["type"])
        vars = {
            "label": node_data["data"]["label"],
            "position": node_data["position"],
            "sourcePosition": node_data.get("sourcePosition", "right"),
            "targetPosition": node_data.get("targetPosition", "left")
        }
        node = Node(node_id, node_type, vars)
        node_map[node_id] = node
        dag.add_node(node)
    
    # Create edges
    for edge_data in data["edges"]:
        source_id = edge_data["source"]
        target_id = edge_data["target"]
        
        if source_id not in node_map or target_id not in node_map:
            raise ValueError(f"Node {source_id} or {target_id} not found")
        source = node_map[source_id]
        target = node_map[target_id]
        edge = Edge(source, target)
        dag.add_edge(edge)

    if not dag.validate():
        raise ValueError("Invalid DAG")
    
    return dag

def load_dag_from_file(file_path: str) -> DAG:
    """
    Load DAG from a file
    Args:
        file_path: Path to the file containing the DAG
    Returns:
        DAG object
    """
    with open(file_path, "r") as f:
        data = f.read()
    return parse_dag(data)

class StartNode(Node):
    def __init__(self, id: str, vars: Dict[str, Any]):
        super().__init__(id, NodeType.START, vars)

class VectorRetriveNode(Node):
    def __init__(self, id: str, vars: Dict[str, Any]):
        self.topk = vars.get("topk", 3)
        self.similarity_score = vars.get("similarity_score", 0.5)
        self.knowledge_base = vars.get("knowledge_base", "")
        super().__init__(id, NodeType.VECTOR_RETRIEVE, vars)

class KeyworkRetriveNode(Node):
    def __init__(self, id: str, vars: Dict[str, Any]):
        self.topk = vars.get("topk", 3)
        self.index = vars.get("index", "")
        super().__init__(id, NodeType.KEYWORD_RETRIEVE, vars)

class RerankNode(Node):
    def __init__(self, id: str, vars: Dict[str, Any]):
        self.topk = vars.get("count", 3)
        self.reverse = vars.get("reverse", False)
        super().__init__(id, NodeType.RERANK, vars)

class LLMChatNode(Node):
    def __init__(self, id: str, vars: Dict[str, Any]):
        self.prompt = vars.get("prompt", "")
        super().__init__(id, NodeType.RERANK, vars)

def walk_func(node: Node, input_ctxs: Dict[Node, Dict[str, Any]], global_ctxs: Dict[Node, Dict[str, Any]]) -> Tuple[Dict[str, Any], bool]:
    """
    Walk the DAG and apply the function to each node
    Returns:
        Tuple[Dict[str, Any], bool]: Tuple of environment variables and boolean indicating if the walk should continue
    """
    return {}, True


def query(query: str, flow: str) -> str:
    dag = parse_dag(flow)
    root = dag.root()
    root.vars["query"] = query
    dag.walk({}, walk_func)
