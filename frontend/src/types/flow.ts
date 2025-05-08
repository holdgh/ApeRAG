import { Edge, Node, Position } from '@xyflow/react';

export type ApeLayoutDirection = 'TB' | 'LR';
export type ApeNodeType = 'global' | 'vector_search' | 'keyword_search' | 'merge' | 'rerank' | 'llm';

export type ApeEdgeTypes = 'straight' | 'step' | 'smoothstep' | 'default' | 'simplebezier'

export type ApeNodeHandlePosition = {
  sourcePosition?: Position;
  targetPosition?: Position;
};


export type ApeNode = Node & {
  data?: {
    vars?: {[key in string]: string | number}[]
  };
};

export type ApeEdge = Edge;
