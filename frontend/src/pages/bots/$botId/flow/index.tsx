import { PageContainer } from '@/components';
import { api } from '@/services';
import {
  ApeEdge,
  ApeEdgeTypes,
  ApeFlow,
  ApeLayoutDirection,
  ApeNode,
  ApeNodeHandlePosition,
} from '@/types';
import { stringifyConfig } from '@/utils';
import Dagre from '@dagrejs/dagre';
import {
  addEdge,
  applyEdgeChanges,
  applyNodeChanges,
  Background,
  BackgroundVariant,
  getConnectedEdges,
  getIncomers,
  getOutgoers,
  OnConnect,
  OnEdgesChange,
  OnNodeDrag,
  OnNodesChange,
  OnNodesDelete,
  OnSelectionChangeFunc,
  Panel,
  Position,
  ReactFlow,
  useReactFlow,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { Button, Divider, GlobalToken, Space, theme, Tooltip } from 'antd';
import alpha from 'color-alpha';
import { useCallback, useEffect, useState } from 'react';
import {
  BsArrowsExpand,
  BsArrowsExpandVertical,
  BsBezier,
  BsClockHistory,
  BsDiagram3,
  BsFullscreenExit,
} from 'react-icons/bs';
import { toast } from 'react-toastify';
import { css, FormattedMessage, styled, useIntl, useModel } from 'umi';
import { v4 as uuidV4 } from 'uuid';
import { stringify } from 'yaml';
import { NodeTypes } from './_nodes';

export const StyledFlowToolbar = styled(Panel).withConfig({
  shouldForwardProp: (prop) => !['token'].includes(prop),
})<{ token: GlobalToken }>`
  ${({ token }) => {
    return css`
      border-radius: ${token.borderRadius}px;
      background: ${alpha(token.colorBgContainer, 0.5)};
      backdrop-filter: blur(10px);
      padding: 4px;
      border: 1px solid ${token.colorBorderSecondary};
      min-width: 200px;
    `;
  }}
`;

export const StyledReactFlow = styled(ReactFlow).withConfig({
  shouldForwardProp: (prop) => !['token'].includes(prop),
})<{ token: GlobalToken }>`
  ${({ token }) => {
    return css`
      --xy-node-color: ${token.colorText}px;
      --xy-node-border-radius: 8px;
      --xy-node-border: 2px solid ${token.colorBorder};
      --xy-node-background-color: ${token.colorBgContainer};
      --xy-node-boxshadow-hover: 0 0 15px ${token.colorBorder};
      --xy-node-boxshadow-selected: 0 0 15px ${token.colorBorder};
      --xy-edge-stroke-width: 2;
      --xy-edge-stroke: ${token.colorBorder};
      --xy-edge-stroke-selected: ${token.colorPrimary};
      --xy-connectionline-stroke: ${token.colorBorder};
      --xy-connectionline-stroke-width: 2;
      --xy-handle-border-color: ${token.colorBorder};
      --xy-handle-background-color: ${token.colorBgContainer};
      .react-flow__node {
        transition:
          border-color 0.3s,
          box-shadow 0.3s;
      }
      .react-flow__node.selected {
        border-color: ${token.colorPrimary};
      }
    `;
  }}
`;

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
  const { themeName } = useModel('global');
  const { bot, getBot } = useModel('bot');

  const [nodes, setNodes] = useState<ApeNode[]>([]);
  const [edges, setEdges] = useState<ApeEdge[]>([]);

  const [edgeType, setEdgeType] = useState<ApeEdgeTypes>('default');
  const [layoutDirection, setLayoutDirection] =
    useState<ApeLayoutDirection>('LR');

  const { fitView } = useReactFlow();

  const { token } = theme.useToken();
  const { formatMessage } = useIntl();

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
      toast.success(formatMessage({ id: 'tips.update.success' }));
    }
  };

  const onSelectionChange: OnSelectionChangeFunc = useCallback(() => {}, []);

  // nodes events
  const onNodesChange: OnNodesChange = useCallback(
    (changes) => setNodes((nds) => applyNodeChanges(changes, nds)),
    [],
  );
  const onNodeDrag: OnNodeDrag = useCallback((e, nd) => {
    setNodes((nds) => {
      return applyNodeChanges(
        [
          {
            id: nd.id,
            type: 'replace',
            item: {
              ...nd,
              selected: false,
            },
          },
        ],
        nds,
      );
    });
  }, []);
  const onNodesDelete: OnNodesDelete = useCallback(
    (deleted) => {
      setEdges(
        deleted.reduce((acc, nd) => {
          const incomers = getIncomers(nd, nodes, edges);
          const outgoers = getOutgoers(nd, nodes, edges);
          const connectedEdges = getConnectedEdges([nd], edges);
          const remainingEdges = acc.filter(
            (edge) => !connectedEdges.includes(edge),
          );
          const createdEdges = incomers.flatMap(({ id: source }) =>
            outgoers.map(({ id: target }) => ({
              id: getEdgeId(source, target),
              source,
              target,
              type: edgeType,
            })),
          );
          return [...remainingEdges, ...createdEdges];
        }, edges),
      );
    },
    [nodes, edges, edgeType],
  );

  // nodes events
  const onEdgesChange: OnEdgesChange = useCallback(
    (changes) => setEdges((eds) => applyEdgeChanges(changes, eds)),
    [],
  );

  const onConnect: OnConnect = useCallback(
    (connection) => {
      setEdges((eds) =>
        addEdge(
          {
            ...connection,
            id: getEdgeId(connection.source, connection.target),
            type: edgeType,
          },
          eds,
        ),
      );
    },
    [edgeType],
  );

  // flow actions
  const setCenterView = useCallback(() => {
    setTimeout(() => {
      fitView({ duration: 300, minZoom: 1, maxZoom: 1 });
    }, 10);
  }, []);

  const setLayout = useCallback(
    (d: ApeLayoutDirection) => {
      const layouted = getLayoutedElements(nodes, edges, {
        direction: d,
      });
      setNodes([...layouted.nodes]);
      setEdges([...layouted.edges]);
      setLayoutDirection(d);
      setCenterView();
    },
    [nodes, edges],
  );

  // remove react flow attribution
  useEffect(() => {
    setCenterView();
    Array.from(
      document.getElementsByClassName('react-flow__attribution'),
    ).forEach((item) => item.remove());
  }, []);

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

  return (
    <PageContainer padding={false} width="auto" height="fixed">
      <StyledReactFlow
        token={token}
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodesDelete={onNodesDelete}
        onSelectionChange={onSelectionChange}
        onNodeDrag={onNodeDrag}
        onConnect={onConnect}
        nodeTypes={NodeTypes}
        colorMode={themeName}
      >
        <Background
          bgColor={token.colorBgLayout}
          color={alpha(token.colorBorder, 0.25)}
          variant={BackgroundVariant.Lines}
          gap={20}
          lineWidth={1}
        />
        <StyledFlowToolbar position="top-right" token={token}>
          <Space split={<Divider type="vertical" style={{ margin: 0 }} />}>
            <Space>
              <Tooltip title={formatMessage({ id: 'flow.edge.smoothstep' })}>
                <Button
                  type="text"
                  icon={<BsDiagram3 />}
                  onClick={() => setEdgeType('smoothstep')}
                />
              </Tooltip>
              <Tooltip title={formatMessage({ id: 'flow.edge.bezier' })}>
                <Button
                  type="text"
                  icon={<BsBezier />}
                  onClick={() => setEdgeType('default')}
                />
              </Tooltip>
            </Space>
            <Space>
              <Tooltip title={formatMessage({ id: 'text.direction.TB' })}>
                <Button
                  type="text"
                  icon={<BsArrowsExpand />}
                  onClick={() => setLayout('TB')}
                />
              </Tooltip>
              <Tooltip title={formatMessage({ id: 'text.direction.LR' })}>
                <Button
                  type="text"
                  icon={<BsArrowsExpandVertical />}
                  onClick={() => setLayout('LR')}
                />
              </Tooltip>
            </Space>
            <Tooltip title={formatMessage({ id: 'action.fitView' })}>
              <Button
                type="text"
                icon={<BsFullscreenExit />}
                onClick={() => setCenterView()}
              />
            </Tooltip>
            <Tooltip title={formatMessage({ id: 'text.history.records' })}>
              <Button type="text" icon={<BsClockHistory />} />
            </Tooltip>

            <Tooltip title={formatMessage({ id: 'action.save' })}>
              <Button type="primary" onClick={saveFlow}>
                <FormattedMessage id="action.save" />
              </Button>
            </Tooltip>
          </Space>
        </StyledFlowToolbar>
        {/* <ApeFlowNodeDetail /> */}
      </StyledReactFlow>
    </PageContainer>
  );
};
