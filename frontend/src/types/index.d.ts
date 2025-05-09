import { Bot, Document } from '@/api';
import { Edge, Node, Position } from '@xyflow/react';

export type Merge<M, N> = Omit<M, Extract<keyof M, keyof N>> & N;

// flow
export type ApeLayoutDirection = 'TB' | 'LR';
export type ApeNodeType =
  | 'global'
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

export type ApeNodeVars = {
  name?: string;
  type?: string;
  description?: string;

  value?: number | string | boolean;
};

export type ApeNode = Node & {
  data?: {
    collapsed?: boolean;
    vars?: ApeNodeVars[];
  };
};

export type ApeEdge = Edge;

/**
 * bots
 */
export type ApeFlow = {
  nodes: ApeNode[];
  edges: ApeEdge[];
  edgeType: ApeEdgeTypes;
  layoutDirection: ApeLayoutDirection;
};
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
