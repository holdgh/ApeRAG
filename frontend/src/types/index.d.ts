import { Bot, Document } from '@/api';
import { Edge, Node, Position } from '@xyflow/react';

export type Merge<M, N> = Omit<M, Extract<keyof M, keyof N>> & N;

// flow
export type ApeLayoutDirection = 'TB' | 'LR';
export type ApeNodeType =
  | 'start'
  | 'vector_search'
  | 'keyword_search'
  | 'merge'
  | 'rerank'
  | 'llm';

export type ApeEdgeTypes =
  | 'straight'
  | 'step'
  | 'smoothstep'
  | 'default'
  | 'simplebezier';

export type ApeNodeHandlePosition = {
  sourcePosition?: Position;
  targetPosition?: Position;
};

export type ApeNodeVar = {
  name?: string;
  type?: string;
  description?: string;

  value?: any;

  global_var?: string;
  source_type?: 'dynamic' | 'global';

  ref_node?: string;
  ref_field?: string;
};

export type ApeNode = Node & {
  collapsed?: boolean;
  data?: {
    collapsed?: boolean;
    vars?: ApeNodeVar[];
  };
};

export type ApeEdge = Edge;

export type ApeNodeConfig = {
  color?: string;
  icon?: React.ReactNode;
  label?: string;
  content?: ({ node }: { node?: ApeNode }) => JSX.Element;
  width?: number;
  disableConnectionTarget?: boolean;
  disableConnectionSource?: boolean;
};
export type ApeNodesConfig = {
  [key in ApeNodeType]: ApeNodeConfig;
};

export type FlowGlobalVariable = {
  name?: string;
  type?: string | number | boolean;
  description?: string;
};

export type FlowExecution = {
  timeout?: number;
  retry?: {
    max_attempts?: number;
    delay?: number;
  };
  error_handling?: {
    strategy?: 'stop_on_error' | 'continue_on_error';
    notification?: {
      email?: string[];
    };
  };
};

export type ApeFlowInfo = {
  name?: string;
  description?: string;
  version?: string;
};

export type ApeFlowStyle = {
  edgeType: ApeEdgeTypes;
  layoutDirection: ApeLayoutDirection;
};

export type ApeFlow = ApeFlowInfo & {
  execution?: FlowExecution;
  global_variables?: ApeNodeVar[];
  nodes: ApeNode[];
  edges: ApeEdge[];
  style: ApeFlowStyle;
};

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
  | 'system'
  | 'local'
  | 's3'
  | 'oss'
  | 'ftp'
  | 'url'
  | 'git'
  | 'email'
  | 'feishu';

export type CollectionEmailSource = 'gmail' | 'outlook' | 'qqmail' | 'others';

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
