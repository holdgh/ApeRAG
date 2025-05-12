import {
  ApeEdge,
  ApeEdgeTypes,
  ApeFlow,
  ApeLayoutDirection,
  ApeNode,
  ApeNodeHandlePosition,
} from '@/types';
import Dagre from '@dagrejs/dagre';
import { Position } from '@xyflow/react';
import { useState } from 'react';
import { v4 as uuidV4 } from 'uuid';

const getNodeHandlePositions = (
  direction: ApeLayoutDirection | undefined = 'LR',
): ApeNodeHandlePosition => {
  const positions: ApeNodeHandlePosition = {};
  switch (direction) {
    case 'TB':
      Object.assign(positions, {
        sourcePosition: Position.Bottom,
        targetPosition: Position.Top,
      });
      break;
    case 'LR':
      Object.assign(positions, {
        sourcePosition: Position.Right,
        targetPosition: Position.Left,
      });
      break;
  }
  return positions;
};

const getLayoutedElements = (
  nodes: ApeNode[],
  edges: ApeEdge[],
  options: { direction: ApeLayoutDirection },
): {
  nodes: ApeNode[];
  edges: ApeEdge[];
} => {
  const direction = options.direction;
  const g = new Dagre.graphlib.Graph().setDefaultEdgeLabel(() => ({}));
  g.setGraph({
    rankdir: direction,
    nodesep: 60,
    ranksep: 100,
  });
  edges.forEach((edge) => g.setEdge(edge.source, edge.target));
  nodes.forEach((node) => {
    g.setNode(node.id, {
      ...node,
      width: node.measured?.width ?? 0,
      height: node.measured?.height ?? 0,
    });
  });
  Dagre.layout(g);
  return {
    nodes: nodes.map((node) => {
      const position = g.node(node.id);
      // We are shifting the dagre node position (anchor=center center) to the top left
      // so it matches the React Flow node anchor point (top left).
      const x = position.x - (node.measured?.width ?? 0) / 2;
      const y = position.y - (node.measured?.height ?? 0) / 2;
      return {
        ...node,
        position: { x, y },
        ...getNodeHandlePositions(direction),
      };
    }),
    edges,
  };
};

const getEdgeId = (sourceId: string, targetId: string): string =>
  `${sourceId}|${targetId}`;

const getInitialData = (): ApeFlow => {
  const globalId = uuidV4();
  const vectorSearchId = uuidV4();
  const keywordSearchId = uuidV4();
  const mergeId = uuidV4();
  const rerankId = uuidV4();
  const llmId = uuidV4();
  return {
    edgeType: 'default',
    layoutDirection: 'LR',
    nodes: [
      {
        id: globalId,
        type: 'global',
        data: {
          vars: [
            {
              name: 'query',
              type: 'string',
              description: "User's question or query",
            },
          ],
        },
        position: { x: 40, y: 300 },
        deletable: false,
        dragHandle: '.drag-handle',
      },
      {
        id: vectorSearchId,
        data: {
          vars: [
            {
              name: 'top_k',
              value: 5,
            },
            {
              name: 'similarity_threshold',
              value: 0.7,
            },
            {
              name: 'query',
              source_type: 'global',
              global_var: 'query',
            },
          ],
        },
        position: { x: 400, y: 200 },
        type: 'vector_search',
        dragHandle: '.drag-handle',
      },
      {
        id: keywordSearchId,
        type: 'keyword_search',
        data: {
          vars: [
            {
              name: 'query',
              source_type: 'global',
              global_var: 'query',
            },
          ],
        },
        position: { x: 400, y: 400 },
        dragHandle: '.drag-handle',
      },
      {
        id: mergeId,
        type: 'merge',
        data: {
          vars: [
            {
              name: 'merge_strategy',
              value: 'union',
            },
            {
              name: 'deduplicate',
              value: true,
            },
            {
              name: 'vector_search_docs',
              source_type: 'dynamic',
              ref_node: '',
              ref_field: '',
            },
            {
              name: 'keyword_search_docs',
              source_type: 'dynamic',
              ref_node: '',
              ref_field: '',
            },
          ],
        },
        position: { x: 700, y: 300 },
        dragHandle: '.drag-handle',
      },
      {
        id: rerankId,
        type: 'rerank',
        data: {
          vars: [
            {
              name: 'model',
              value: '',
            },
            {
              name: 'docs',
              source_type: 'dynamic',
              ref_node: '',
              ref_field: '',
            },
          ],
        },
        position: { x: 1000, y: 300 },
        dragHandle: '.drag-handle',
      },
      {
        id: llmId,
        type: 'llm',
        data: {
          vars: [
            {
              name: 'model',
              value: 'gpt-3.5-turbo',
            },
            {
              name: 'temperature',
              value: 0.7,
            },
            {
              name: 'max_tokens',
              value: 1000,
            },
            {
              name: 'query',
              source_type: 'global',
              global_var: 'query',
            },
            {
              name: 'docs',
              source_type: 'dynamic',
              ref_node: '',
              ref_field: '',
            },
          ],
        },
        position: { x: 1300, y: 300 },
        dragHandle: '.drag-handle',
      },
    ],
    edges: [
      {
        id: getEdgeId(globalId, vectorSearchId),
        source: globalId,
        target: vectorSearchId,
        type: 'default',
      },
      {
        id: getEdgeId(globalId, keywordSearchId),
        source: globalId,
        target: keywordSearchId,
        type: 'default',
      },
      {
        id: getEdgeId(vectorSearchId, mergeId),
        source: vectorSearchId,
        target: mergeId,
        type: 'default',
      },
      {
        id: getEdgeId(keywordSearchId, mergeId),
        source: keywordSearchId,
        target: mergeId,
        type: 'default',
      },
      {
        id: getEdgeId(mergeId, rerankId),
        source: mergeId,
        target: rerankId,
        type: 'default',
      },
      {
        id: getEdgeId(rerankId, llmId),
        source: rerankId,
        target: llmId,
        type: 'default',
      },
    ],
  };
};

export default () => {
  const [nodes, setNodes] = useState<ApeNode[]>([]);
  const [edges, setEdges] = useState<ApeEdge[]>([]);
  const [edgeType, setEdgeType] = useState<ApeEdgeTypes>('default');
  const [layoutDirection, setLayoutDirection] =
    useState<ApeLayoutDirection>('LR');

  return {
    nodes,
    setNodes,

    edges,
    setEdges,

    edgeType,
    setEdgeType,

    layoutDirection,
    setLayoutDirection,

    getLayoutedElements,
    getInitialData,
    getEdgeId,
  };
};
