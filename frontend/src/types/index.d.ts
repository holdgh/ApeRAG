import { Bot, Document, NodeDataOutput, NodeDataInput } from "@/api";
import { Edge, Node, Position } from "@xyflow/react";

export type Merge<M, N> = Omit<M, Extract<keyof M, keyof N>> & N;

// flow
export type ApeLayoutDirection = "TB" | "LR";
export type ApeNodeType =
  | "start"
  | "vector_search"
  | "keyword_search"
  | "merge"
  | "rerank"
  | "llm";

export type ApeEdgeTypes =
  | "straight"
  | "step"
  | "smoothstep"
  | "default"
  | "simplebezier";

export type ApeNodeHandlePosition = {
  sourcePosition?: Position;
  targetPosition?: Position;
};

export type ApeNode = Node & {
  position?: {
    x?: number;
    y?: number;
  };
  dragHandle: string;
  measured: {
    width?: number;
    height?: number;
  };
  selected?: boolean;
  deletable?: boolean;
  data?: {
    collapsed?: boolean;

    input?: NodeDataInput;
    output?: NodeDataOutput;
  };
};

export type ApeEdge = Edge;

export type ApeNodeConfig = {
  color?: string;
  icon?: React.ReactNode;
  label?: string;
  content?: ({ node }: { node: ApeNode }) => JSX.Element;
  width?: number;
  disableConnectionTarget?: boolean;
  disableConnectionSource?: boolean;
};

export type ApeNodesConfig = {
  [key in ApeNodeType]: ApeNodeConfig;
};

export type ApeFlowStyle = {
  edgeType: ApeEdgeTypes;
  layoutDirection: ApeLayoutDirection;
};

export type ApeFlow = ApeFlowInfo & {
  name?: string;
  title?: string;
  description?: string;
  version?: string;

  execution?: ExecutionConfig;
  schema?: { [key: string]: SchemaDefinition };

  nodes: ApeNode[];
  edges: ApeEdge[];

  style: ApeFlowStyle;
};

// to delete
export type ApeFlowNodeOutput = {
  doc_id?: string;
  rank_before?: number;
  score?: number;
  source?: string;
  text?: string;
  metadata?: {
    chunk_num?: number;
    content_ratio?: number;
    name?: string;
    object_path?: string;
    source?: string;
  };
};

export type ApeFlowDebugInfo = {
  event_type:
    | "flow_start"
    | "node_start"
    | "node_end"
    | "flow_end"
    | "output_chunk";
  node_id: string;
  execution_id: string;
  timestamp: string;
  data: {
    flow_id: string;
    node_type?: string;
    inputs?: any;
    outputs?: {
      docs: ApeFlowNodeOutput[];
      keyword_search_docs: ApeFlowNodeOutput[];
      vector_search_docs: ApeFlowNodeOutput[];
    };
  };
};

export type ApeFlowStatus = "running" | "completed" | "stopped";
export type ApeFlowNodeStatus = "pending" | "running" | "complated" | "stopped";

/**
 * bots
 */
export type BotConfig = {
  flow?: ApeFlow;
  model?: string;
  model_service_provider?: string;
  model_name?: string;
  charactor?: string;
  llm?: {
    similarity_score_threshold?: number;
    similarity_topk?: number;
    context_window?: number;
    prompt_template?: string;
    temperature?: number;
    memory_prompt_template: string;
  };
  memory: boolean;
  use_related_question: boolean;
  feishu?: {
    encrypt_key?: string;
  };
};

export type ApeBot = Merge<Bot, { config?: BotConfig }>;

/**
 * collection
 */
export type CollectionConfigSource =
  | "system"
  | "local"
  | "s3"
  | "oss"
  | "ftp"
  | "url"
  | "git"
  | "email"
  | "feishu";

export type CollectionEmailSource = "gmail" | "outlook" | "qqmail" | "others";

/**
 * documents
 */
export type ApeDocumentConfig = {
  path?: string;
  labels?: {
    [key in string]: string;
  }[];
};

export type ApeDocument = Merge<Document, { config?: ApeDocumentConfig }>;
