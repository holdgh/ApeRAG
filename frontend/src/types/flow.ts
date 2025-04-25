import { Edge, Node, Position } from '@xyflow/react';

export type LayoutDirection = 'TB' | 'LR';
export type ApeNodeType = 'start' | 'end' | 'normal';

export type NodeHandlePosition = {
  sourcePosition?: Position;
  targetPosition?: Position;
};

export type ApeNode = Node & {
  data?: {
    label?: string;
  };
};

export type ApeEdge = Edge;
