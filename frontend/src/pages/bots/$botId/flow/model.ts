import {
  ApeEdge,
  ApeFlowDebugInfo,
  ApeFlowStatus,
  ApeNode,
  ApeNodeConfig,
  ApeNodeHandlePosition,
  ApeNodesConfig,
  ApeNodeType,
} from "@/types";
import {
  FunnelPlotOutlined,
  HomeOutlined,
  InteractionOutlined,
  MergeOutlined,
  ReadOutlined,
  WechatWorkOutlined,
} from "@ant-design/icons";
import Dagre from "@dagrejs/dagre";
import { Position } from "@xyflow/react";
import { theme } from "antd";
import React, { useEffect, useState } from "react";
import uniqid from "uniqid";

import { ApeNodeKeywordSearch } from "../flow/_nodes/_node_keyword_search";
import { ApeNodeLlm } from "../flow/_nodes/_node_llm";
import { ApeNodeMerge } from "../flow/_nodes/_node_merge";
import { ApeNodeRerank } from "../flow/_nodes/_node_rerank";
import { ApeNodeStart } from "../flow/_nodes/_node_start";
import { ApeNodeVectorSearch } from "../flow/_nodes/_node_vector_search";
import {
  getNodeKeywordSearchInitData,
  getNodeLlmInitData,
  getNodeMergeNodeInitData,
  getNodeRerankInitData,
  getNodeStartInitData,
  getNodeVectorSearchInitData,
} from "./node_definition";
import { WorkflowDefinition, WorkflowStyle } from "@/api";

const getNodeHandlePositions = (
  direction: WorkflowStyle["layoutDirection"] | undefined = "LR"
): ApeNodeHandlePosition => {
  const positions: ApeNodeHandlePosition = {};
  switch (direction) {
    case "TB":
      Object.assign(positions, {
        sourcePosition: Position.Bottom,
        targetPosition: Position.Top,
      });
      break;
    case "LR":
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
  options: { direction: WorkflowStyle["layoutDirection"] }
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

const getEdgeId = (): string => uniqid();

const getInitialData = (): WorkflowDefinition => {
  const startId = uniqid();
  const vectorSearchId = uniqid();
  const keywordSearchId = uniqid();
  const mergeId = uniqid();
  const rerankId = uniqid();
  const llmId = uniqid();

  return {
    name: "rag_flow",
    title: "RAG Knowledge Base Flow",
    description: "A typical RAG flow with parallel retrieval and reranking",
    version: "1.0.0",
    execution: {
      timeout: 300,
      retry: {
        max_attempts: 3,
        delay: 5,
      },
      error_handling: {
        strategy: "stop_on_error",
        notification: {
          email: ["admin@example.com"],
        },
      },
    },
    schema: {
      document_with_score: {
        type: "object",
        properties: {
          doc_id: {
            type: "string",
          },
          text: {
            type: "string",
          },
          score: {
            type: "number",
          },
          metadata: {
            type: "object",
          },
        },
      },
    },
    nodes: [
      {
        id: startId,
        type: "start",
        data: getNodeStartInitData(),
        position: { x: 0, y: 332 },
        deletable: false,
        dragHandle: ".drag-handle",
      },
      {
        id: vectorSearchId,
        data: getNodeVectorSearchInitData(startId),
        position: { x: 422, y: -100 },
        type: "vector_search",
        dragHandle: ".drag-handle",
        deletable: false,
      },
      {
        id: keywordSearchId,
        type: "keyword_search",
        data: getNodeKeywordSearchInitData(startId),
        position: { x: 422, y: 460 },
        dragHandle: ".drag-handle",
        deletable: false,
      },
      {
        id: mergeId,
        type: "merge",
        data: getNodeMergeNodeInitData(vectorSearchId, keywordSearchId),
        position: { x: 884, y: 212 },
        dragHandle: ".drag-handle",
        deletable: false,
      },
      {
        id: rerankId,
        type: "rerank",
        data: getNodeRerankInitData(mergeId),
        position: { x: 1286, y: 298 },
        dragHandle: ".drag-handle",
        deletable: false,
      },
      {
        id: llmId,
        type: "llm",
        data: getNodeLlmInitData(startId, rerankId),
        position: { x: 1688, y: 133.5 },
        dragHandle: ".drag-handle",
        deletable: false,
      },
    ],
    edges: [
      {
        id: getEdgeId(),
        source: startId,
        target: vectorSearchId,
        type: "default",
      },
      {
        id: getEdgeId(),
        source: startId,
        target: keywordSearchId,
        type: "default",
      },
      {
        id: getEdgeId(),
        source: vectorSearchId,
        target: mergeId,
        type: "default",
      },
      {
        id: getEdgeId(),
        source: keywordSearchId,
        target: mergeId,
        type: "default",
      },
      {
        id: getEdgeId(),
        source: mergeId,
        target: rerankId,
        type: "default",
        deletable: false,
      },
      {
        id: getEdgeId(),
        source: rerankId,
        target: llmId,
        type: "default",
      },
    ],
    style: {
      edgeType: "default",
      layoutDirection: "LR",
    },
  };
};

export default () => {
  // flow data
  const [nodes, setNodes] = useState<ApeNode[]>([]);
  const [edges, setEdges] = useState<ApeEdge[]>([]);
  const [flowStyle, setFlowStyle] = useState<WorkflowStyle>({
    edgeType: "default",
    layoutDirection: "LR",
  });

  // debug state
  const [flowStatus, setFlowStatus] = useState<ApeFlowStatus>("stopped");
  const [messages, setMessages] = useState<ApeFlowDebugInfo[]>([]);

  const { token } = theme.useToken();

  const getNodeConfig = (
    nodeType?: ApeNodeType,
    label?: string
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
    if (flowStatus === "stopped") {
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

    getLayoutedElements,
    getInitialData,
    getEdgeId,
    getNodeConfig,
  };
};
