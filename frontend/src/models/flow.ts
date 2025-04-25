import { ApeEdge, ApeNode, LayoutDirection } from '@/types/flow';
import { useCallback, useEffect, useState } from 'react';
import { v4 as uuidV4 } from 'uuid';
import { stringify } from 'yaml';

const getEdgeId = (sourceId: string, targetId: string): string =>
  `${sourceId}|${targetId}`;
const getNodeId = (): string => uuidV4();

const startId = uuidV4();
const midId = uuidV4();
const endId = uuidV4();
const getInitialData = () => {
  return {
    nodes: [
      {
        id: startId,
        type: 'start',
        data: { label: '开始' },
        position: { x: 100, y: 300 },
        deletable: false,
      },
      {
        id: midId,
        data: { label: 'LLM' },
        position: { x: 500, y: 200 },
        type: 'normal',
      },
      {
        id: endId,
        type: 'end',
        data: { label: '结束' },
        position: { x: 900, y: 400 },
        deletable: false,
      },
    ],
    edges: [
      {
        id: getEdgeId(startId, midId),
        source: startId,
        target: midId,
        type: 'default',
      },
      {
        id: getEdgeId(midId, endId),
        source: midId,
        target: endId,
        type: 'default',
      },
    ],
  };
};

type EdgeTypes =
  | 'straight'
  | 'step'
  | 'smoothstep'
  | 'default'
  | 'simplebezier';

export default () => {
  const [nodes, setNodes] = useState<ApeNode[]>([]);
  const [edges, setEdges] = useState<ApeEdge[]>([]);
  const [edgeType, setEdgeType] = useState<EdgeTypes>('default');
  const [layoutDirection, setLayoutDirection] = useState<LayoutDirection>('LR');

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
