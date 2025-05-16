import {
  ApeEdge,
  ApeFlow,
  ApeFlowInfo,
  ApeFlowStyle,
  ApeLayoutDirection,
  ApeNode,
  ApeNodeConfig,
  ApeNodeHandlePosition,
  ApeNodesConfig,
  ApeNodeType,
  ApeNodeVar,
  FlowExecution,
} from '@/types';
import {
  FunnelPlotOutlined,
  HomeOutlined,
  InteractionOutlined,
  MergeOutlined,
  ReadOutlined,
  WechatWorkOutlined,
} from '@ant-design/icons';
import Dagre from '@dagrejs/dagre';
import { Position } from '@xyflow/react';
import { theme } from 'antd';
import _ from 'lodash';
import React, { useState } from 'react';
import { v4 as uuidV4 } from 'uuid';

import { ApeNodeKeywordSearch } from '../flow/_nodes/_node_keyword_search';
import { ApeNodeLlm } from '../flow/_nodes/_node_llm';
import { ApeNodeMerge } from '../flow/_nodes/_node_merge';
import { ApeNodeRerank } from '../flow/_nodes/_node_rerank';
import { ApeNodeStart } from '../flow/_nodes/_node_start';
import { ApeNodeVectorSearch } from '../flow/_nodes/_node_vector_search';

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

const getEdgeId = (): string => uuidV4();

const getInitialData = (): ApeFlow => {
  const globalId = uuidV4();
  const vectorSearchId = uuidV4();
  const keywordSearchId = uuidV4();
  const mergeId = uuidV4();
  const rerankId = uuidV4();
  const llmId = uuidV4();

  return {
    name: 'RAG Knowledge Base Flow',
    description: 'A typical RAG flow with parallel retrieval and reranking',
    version: '1.0.0',
    execution: {
      timeout: 300,
      retry: {
        max_attempts: 3,
        delay: 5,
      },
      error_handling: {
        strategy: 'stop_on_error',
        notification: {
          email: ['admin@example.com'],
        },
      },
    },
    global_variables: [
      {
        name: 'query',
        type: 'string',
        description: "User's question or query",
      },
    ],
    nodes: [
      {
        id: globalId,
        type: 'start',
        data: {},
        position: { x: 0, y: 332 },
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
              value: 0.2,
            },
            {
              name: 'collection_ids',
              value: [],
            },
            {
              name: 'query',
              source_type: 'global',
              global_var: 'query',
            },
          ],
        },
        position: { x: 422, y: 439 },
        type: 'vector_search',
        dragHandle: '.drag-handle',
      },
      {
        id: keywordSearchId,
        type: 'keyword_search',
        data: {
          vars: [
            {
              name: 'collection_ids',
              value: [],
            },
            {
              name: 'query',
              source_type: 'global',
              global_var: 'query',
            },
          ],
        },
        position: { x: 422, y: 0 },
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
              ref_node: vectorSearchId,
              ref_field: 'vector_search_docs',
            },
            {
              name: 'keyword_search_docs',
              source_type: 'dynamic',
              ref_node: keywordSearchId,
              ref_field: 'keyword_search_docs',
            },
          ],
        },
        position: { x: 884, y: 212 },
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
              ref_node: mergeId,
              ref_field: 'docs',
            },
          ],
        },
        position: { x: 1286, y: 298 },
        dragHandle: '.drag-handle',
      },
      {
        id: llmId,
        type: 'llm',
        data: {
          vars: [
            {
              name: 'model',
              value: '',
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
              ref_node: rerankId,
              ref_field: 'docs',
            },
          ],
        },
        position: { x: 1688, y: 133.5 },
        dragHandle: '.drag-handle',
      },
    ],
    edges: [
      {
        id: getEdgeId(),
        source: globalId,
        target: vectorSearchId,
        type: 'default',
      },
      {
        id: getEdgeId(),
        source: globalId,
        target: keywordSearchId,
        type: 'default',
      },
      {
        id: getEdgeId(),
        source: vectorSearchId,
        target: mergeId,
        type: 'default',
      },
      {
        id: getEdgeId(),
        source: keywordSearchId,
        target: mergeId,
        type: 'default',
      },
      {
        id: getEdgeId(),
        source: mergeId,
        target: rerankId,
        type: 'default',
      },
      {
        id: getEdgeId(),
        source: rerankId,
        target: llmId,
        type: 'default',
      },
    ],
    style: {
      edgeType: 'default',
      layoutDirection: 'LR',
    },
  };
};

export default () => {
  const [flowInfo, setFlowInfo] = useState<ApeFlowInfo>();
  const [globalVariables, setGlobalVariables] = useState<ApeNodeVar[]>();
  const [execution, setExecution] = useState<FlowExecution>();
  const [nodes, setNodes] = useState<ApeNode[]>([]);
  const [edges, setEdges] = useState<ApeEdge[]>([]);
  const { token } = theme.useToken();

  const [flowStyle, setFlowStyle] = useState<ApeFlowStyle>({
    edgeType: 'default',
    layoutDirection: 'LR',
  });

  const getNodeOutputVars = (node?: ApeNode): ApeNodeVar[] | undefined => {
    if (!node) return globalVariables;
    switch (node.type) {
      case 'vector_search':
        return node.data.vars?.filter(
          (item) =>
            !_.includes(
              ['top_k', 'similarity_threshold', 'collection_ids'],
              item.name,
            ),
        );
      case 'keyword_search':
        return node.data.vars?.filter(
          (item) => !_.includes(['collection_ids'], item.name),
        );
      case 'llm':
        return node.data.vars?.filter(
          (item) =>
            !_.includes(
              ['model', 'temperature', 'max_tokens', 'docs'],
              item.name,
            ),
        );
      default:
        return node.data.vars;
    }
  };

  const getNodeConfig = (
    nodeType?: ApeNodeType,
    label?: string,
  ): ApeNodeConfig => {
    if (!nodeType) return {};
    const configs: ApeNodesConfig = {
      start: {
        color: token.cyan,
        icon: React.createElement(HomeOutlined),
        content: ApeNodeStart,
        width: 320,
        disableConnectionTarget: true,
      },
      vector_search: {
        color: token.orange,
        icon: React.createElement(InteractionOutlined),
        content: ApeNodeVectorSearch,
        width: 360,
      },
      keyword_search: {
        color: token.volcano,
        icon: React.createElement(ReadOutlined),
        content: ApeNodeKeywordSearch,
        width: 360,
      },
      merge: {
        color: token.purple,
        icon: React.createElement(MergeOutlined),
        content: ApeNodeMerge,
        width: 300,
      },
      rerank: {
        color: token.magenta,
        icon: React.createElement(FunnelPlotOutlined),
        content: ApeNodeRerank,
        width: 300,
      },
      llm: {
        color: token.blue,
        icon: React.createElement(WechatWorkOutlined),
        content: ApeNodeLlm,
        width: 320,
        disableConnectionSource: true,
      },
    };
    return {
      ...configs[nodeType],
      label,
    };
  };

  return {
    flowInfo,
    setFlowInfo,

    execution,
    setExecution,

    globalVariables,
    setGlobalVariables,

    nodes,
    setNodes,

    edges,
    setEdges,

    flowStyle,
    setFlowStyle,

    getLayoutedElements,
    getInitialData,
    getEdgeId,
    getNodeOutputVars,
    getNodeConfig,
  };
};
