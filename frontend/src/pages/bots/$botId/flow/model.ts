import {
  ApeEdge,
  ApeFlowDebugInfo,
  ApeFlowStatus,
  ApeNode,
  ApeNodeConfig,
  ApeNodesConfig,
} from '@/types';
import {
  FunnelPlotOutlined,
  HomeOutlined,
  InteractionOutlined,
  MergeOutlined,
  ReadOutlined,
  WechatWorkOutlined,
} from '@ant-design/icons';

import { NodeTypeEnum, WorkflowStyle } from '@/api';
import { theme } from 'antd';
import React, { useEffect, useState } from 'react';
import { ApeNodeKeywordSearch } from '../flow/_nodes/_node_keyword_search';
import { ApeNodeLlm } from '../flow/_nodes/_node_llm';
import { ApeNodeMerge } from '../flow/_nodes/_node_merge';
import { ApeNodeRerank } from '../flow/_nodes/_node_rerank';
import { ApeNodeStart } from '../flow/_nodes/_node_start';
import { ApeNodeVectorSearch } from '../flow/_nodes/_node_vector_search';

export default () => {
  // flow data
  const [nodes, setNodes] = useState<ApeNode[]>([]);
  const [edges, setEdges] = useState<ApeEdge[]>([]);
  const [flowStyle, setFlowStyle] = useState<WorkflowStyle>({
    edgeType: 'default',
    layoutDirection: 'LR',
  });

  // debug state
  const [flowStatus, setFlowStatus] = useState<ApeFlowStatus>('stopped');
  const [messages, setMessages] = useState<ApeFlowDebugInfo[]>([]);

  const { token } = theme.useToken();

  const getNodeConfig = (
    nodeType?: NodeTypeEnum,
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
        width: 330,
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
        width: 440,
        disableConnectionSource: true,
      },
    };
    return {
      ...configs[nodeType],
      label,
    };
  };

  useEffect(() => {
    if (flowStatus === 'stopped') {
      setMessages([]);
    }
  }, [flowStatus]);

  return {
    nodes,
    setNodes,

    edges,
    setEdges,

    flowStyle,
    setFlowStyle,

    flowStatus,
    setFlowStatus,

    messages,
    setMessages,

    getNodeConfig,
  };
};
