import { api } from '@/services';
import {
  ApeEdge,
  ApeEdgeTypes,
  ApeFlow,
  ApeLayoutDirection,
  ApeNode,
} from '@/types';
import { stringifyConfig } from '@/utils';
import { useEffect, useState } from 'react';
import { useModel } from 'umi';
import { v4 as uuidV4 } from 'uuid';
import { stringify } from 'yaml';

const getEdgeId = (sourceId: string, targetId: string): string =>
  `${sourceId}|${targetId}`;
const getNodeId = (): string => uuidV4();

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
          vars: [],
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
      },
      {
        id: mergeId,
        type: 'merge',
        data: {},
        position: { x: 700, y: 300 },
      },
      {
        id: rerankId,
        type: 'rerank',
        data: {},
        position: { x: 1000, y: 300 },
      },
      {
        id: llmId,
        type: 'llm',
        data: {},
        position: { x: 1300, y: 300 },
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
  const { bot, getBot } = useModel('bot');
  const [nodes, setNodes] = useState<ApeNode[]>([]);
  const [edges, setEdges] = useState<ApeEdge[]>([]);
  const [edgeType, setEdgeType] = useState<ApeEdgeTypes>('default');
  const [layoutDirection, setLayoutDirection] =
    useState<ApeLayoutDirection>('LR');

  const saveFlow = async () => {
    if (!bot?.id) return;
    const flow = stringify({
      nodes,
      edges,
      edgeType,
      layoutDirection,
    });
    const config = { ...bot.config, flow };
    const res = await api.botsBotIdPut({
      botId: bot.id,
      botUpdate: {
        ...bot,
        config: stringifyConfig(config),
      },
    });
    if (res.status === 200) {
      getBot(bot.id);
    }
  };

  useEffect(() => {
    setEdges((eds) => eds.map((edge) => ({ ...edge, type: edgeType })));
  }, [edgeType]);

  useEffect(() => {
    const flow = bot?.config?.flow || getInitialData();
    setNodes(flow.nodes);
    setEdges(flow.edges);
    setEdgeType(flow.edgeType);
    setLayoutDirection(flow.layoutDirection);
  }, [bot]);

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
