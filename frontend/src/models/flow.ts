import { ApeEdge, ApeNode, ApeLayoutDirection, ApeEdgeTypes } from '@/types/flow';
import { useCallback, useEffect, useState } from 'react';
import { v4 as uuidV4 } from 'uuid';
import { stringify } from 'yaml';

const getEdgeId = (sourceId: string, targetId: string): string =>
  `${sourceId}|${targetId}`;
const getNodeId = (): string => uuidV4();

const globalId = uuidV4();
const vectorSearchId = uuidV4();
const keywordSearchId = uuidV4();
const mergeId = uuidV4();
const rerankId = uuidV4();
const llmId = uuidV4();

const nodes: ApeNode[] = [
  {
    id: globalId,
    type: 'global',
    data: {
      vars: []
    },
    position: { x: 100, y: 300 },
    deletable: false,
  },
  {
    id: vectorSearchId,
    data: {},
    position: { x: 400, y: 200 },
    type: 'vector_search',
  },
  {
    id: keywordSearchId,
    type: 'keyword_search',
    data: {},
    position: { x: 400, y: 400 },
    deletable: false,
  },
  {
    id: mergeId,
    type: 'merge',
    data: {},
    position: { x: 700, y: 300 },
    deletable: false,
  },
  {
    id: rerankId,
    type: 'rerank',
    data: {},
    position: { x: 1000, y: 300 },
    deletable: false,
  },
  {
    id: llmId,
    type: 'llm',
    data: {},
    position: { x: 1300, y: 300 },
    deletable: false,
  },
]

const getInitialData = () => {
  return {
    nodes: nodes,
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
  const [layoutDirection, setLayoutDirection] = useState<ApeLayoutDirection>('LR');

  const saveFlow = useCallback(() => {
    console.log(
      stringify({
        nodes,
        edges,
        edgeType,
        layoutDirection,
      }),
    );
  }, [nodes, edges, edgeType, layoutDirection]);

  useEffect(() => {
    setEdges((eds) => eds.map((edge) => ({ ...edge, type: edgeType })));
  }, [edgeType]);

  useEffect(() => {
    const { nodes, edges } = getInitialData();
    setNodes(nodes);
    setEdges(edges);
  }, []);

  return {
    nodes,
    setNodes,

    edges,
    setEdges,

    edgeType,
    setEdgeType,

    layoutDirection,
    setLayoutDirection,

    saveFlow,

    getEdgeId,
    getNodeId,
  };
};
