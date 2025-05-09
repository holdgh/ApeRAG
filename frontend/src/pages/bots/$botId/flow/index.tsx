import { PageContainer } from '@/components';
import {
  ApeEdge,
  ApeLayoutDirection,
  ApeNode,
  ApeNodeHandlePosition,
  ApeNodeType,
} from '@/types';
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
import { useCallback, useEffect, useMemo } from 'react';

import {
  BsArrowsExpand,
  BsArrowsExpandVertical,
  BsBezier,
  BsClockHistory,
  BsDiagram3,
  BsFullscreenExit,
} from 'react-icons/bs';
import { css, FormattedMessage, styled, useIntl, useModel } from 'umi';
import { ApeFlowNode } from './_flow_node';
// import { ApeFlowNodeDetail } from './_flow_node_detail';

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

export default () => {
  const {
    nodes,
    edges,
    setNodes,
    setEdges,
    edgeType,
    setLayoutDirection,
    setEdgeType,
    saveFlow,
    getEdgeId,
  } = useModel('flow');
  const { fitView } = useReactFlow();
  const { themeName } = useModel('global');
  const { token } = theme.useToken();
  const { formatMessage } = useIntl();

  const nodeTypes: { [key in ApeNodeType]: any } = useMemo(
    () => ({
      global: ApeFlowNode,
      vector_search: ApeFlowNode,
      keyword_search: ApeFlowNode,
      merge: ApeFlowNode,
      rerank: ApeFlowNode,
      llm: ApeFlowNode,
    }),
    [],
  );

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
        nodeTypes={nodeTypes}
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
