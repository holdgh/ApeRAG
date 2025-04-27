import { Edge, Node, Position } from '@xyflow/react';

export type ApeLayoutDirection = 'TB' | 'LR';
export type ApeNodeType = 'start' | 'end' | 'normal';

export type ApeNodeHandlePosition = {
  sourcePosition?: Position;
  targetPosition?: Position;
};

export type ApeNode = Node & {
  data?: {
    label?: string;
  };
};

export type ApeEdge = Edge;
