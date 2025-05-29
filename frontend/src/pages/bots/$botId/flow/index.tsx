import { PageContainer } from '@/components';
import { api } from '@/services';
import { ApeEdge, ApeFlowDebugInfo, ApeNode } from '@/types';

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
  ReactFlow,
  useReactFlow,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import {
  Button,
  Divider,
  Form,
  GlobalToken,
  Input,
  Modal,
  Space,
  theme,
  Tooltip,
} from 'antd';
import alpha from 'color-alpha';
import { useCallback, useEffect, useState } from 'react';
import {
  BsArrowsExpand,
  BsArrowsExpandVertical,
  BsBezier,
  BsClockHistory,
  BsDiagram3,
  BsFullscreenExit,
  BsPauseFill,
  BsPlayFill,
} from 'react-icons/bs';
import { toast } from 'react-toastify';
import { css, FormattedMessage, styled, useIntl, useModel } from 'umi';
import uniqid from "uniqid";

import { WorkflowDefinition, WorkflowStyle } from '@/api';
import { EventSourceParserStream } from 'eventsource-parser/stream';
import { stringify } from 'yaml';
import { NodeTypes } from './_nodes';
import { getInitialData, getLayoutedElements } from './utils';

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

export default () => {
  const { themeName } = useModel('global');
  const { bot } = useModel('bot');
  const { getAvailableModels } = useModel('models');
  const { getCollections } = useModel('collection');

  const {
    nodes,
    setEdges,

    edges,
    setNodes,

    flowStyle,
    setFlowStyle,

    setMessages,

    flowStatus,
    setFlowStatus,
  } = useModel('bots.$botId.flow.model');

  const { fitView } = useReactFlow();
  const { token } = theme.useToken();
  const { formatMessage } = useIntl();
  const [debugForm] = Form.useForm<{ query: string }>();
  const [debugVisible, setDebugVisible] = useState<boolean>(false);

  const getFlow = async () => {
    if (!bot?.id) return;
    const flowDefault = getInitialData();
    const { data } = await api.botsBotIdFlowGet({ botId: bot.id });
    setNodes((data?.nodes || flowDefault.nodes) as ApeNode[]);
    setEdges((data?.edges || flowDefault.edges) as ApeEdge[]);
    setFlowStyle(
      data?.style ||
        flowDefault.style || {
          edgeType: 'default',
          layoutDirection: 'LR',
        },
    );
  };

  const saveFlow = async () => {
    if (!bot?.id) return;
    const flow: WorkflowDefinition = {
      ...getInitialData(),
      nodes,
      edges,
      style: flowStyle,
    };
    console.log(stringify(flow));

    const res = await api.botsBotIdFlowPut({
      botId: bot.id,
      workflowDefinition: flow,
    });

    if (res.status === 200) {
      toast.success(formatMessage({ id: 'tips.update.success' }));
    }
  };

  const debug = async () => {
    if (!bot?.id) return;
    const { query } = await debugForm.validateFields();
    setDebugVisible(false);
    setFlowStatus('running');
    const response = await api.botsBotIdFlowDebugPost(
      {
        botId: bot.id,
        debugFlowRequest: { query },
      },
      {
        responseType: 'stream',
        adapter: 'fetch',
        timeout: 600 * 1000,
      },
    );
    const stream = response.data as unknown as ReadableStream;
    const reader = stream
      .pipeThrough(new TextDecoderStream())
      .pipeThrough(new EventSourceParserStream())
      .getReader();
    while (true) {
      const { value, done } = await reader.read();
      if (done) {
        console.log('reader done');
        break;
      };
      try {
        const msg: ApeFlowDebugInfo = JSON.parse(value.data);
        console.log(msg);
        if (msg.event_type === 'flow_end') {
          setFlowStatus('completed');
        }
        setMessages((msgs) => [...msgs, msg]);
      } catch (err) {
        console.log('msg parse error', err);
      }
    }
  };

  const onSelectionChange: OnSelectionChangeFunc = useCallback(() => {}, []);

  // nodes events
  const onNodesChange: OnNodesChange = useCallback(
    (changes) => setNodes((nds) => applyNodeChanges(changes, nds) as ApeNode[]),
    [],
  );
  const onNodeDrag: OnNodeDrag = useCallback(() => {}, []);
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
          const createdEdges = incomers.flatMap(
            ({ id: source }) =>
              outgoers.map(({ id: target }) => ({
                id: uniqid(),
                source,
                target,
                type: flowStyle.edgeType,
              })) as ApeEdge[],
          );
          return [...remainingEdges, ...createdEdges];
        }, edges) as ApeEdge[],
      );
    },
    [nodes, edges, flowStyle],
  );

  // nodes events
  const onEdgesChange: OnEdgesChange = useCallback(
    (changes) => setEdges((eds) => applyEdgeChanges(changes, eds) as ApeEdge[]),
    [],
  );

  const onConnect: OnConnect = useCallback(
    (connection) => {
      setEdges((eds) =>
        addEdge(
          {
            ...connection,
            id: uniqid(),
            type: flowStyle.edgeType,
          },
          eds,
        ),
      );
    },
    [flowStyle],
  );

  // flow actions
  const setCenterView = useCallback(() => {
    setTimeout(() => {
      fitView({ duration: 300, maxZoom: 1 });
    }, 10);
  }, []);

  const setLayout = useCallback(
    (d: WorkflowStyle['layoutDirection']) => {
      const layouted = getLayoutedElements(nodes, edges, {
        direction: d,
      });
      setNodes([...layouted.nodes]);
      setEdges([...layouted.edges]);
      setFlowStyle((s) => ({ ...s, layoutDirection: d }));
      setCenterView();
    },
    [nodes, edges],
  );

  useEffect(() => {
    getCollections();
  }, []);

  // remove react flow attribution
  useEffect(() => {
    setCenterView();
    Array.from(
      document.getElementsByClassName('react-flow__attribution'),
    ).forEach((item) => item.remove());
  }, []);

  useEffect(() => {
    setEdges(
      (eds) =>
        eds.map((edge) => ({ ...edge, type: flowStyle.edgeType })) as ApeEdge[],
    );
  }, [flowStyle]);

  useEffect(() => {
    getAvailableModels();
    getFlow();
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
                  onClick={() =>
                    setFlowStyle((s) => ({ ...s, edgeType: 'smoothstep' }))
                  }
                />
              </Tooltip>
              <Tooltip title={formatMessage({ id: 'flow.edge.bezier' })}>
                <Button
                  type="text"
                  icon={<BsBezier />}
                  onClick={() =>
                    setFlowStyle((s) => ({ ...s, edgeType: 'default' }))
                  }
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

            <Tooltip title={formatMessage({ id: 'action.debug' })}>
              <Button
                type={flowStatus === 'running' ? 'primary' : 'text'}
                onClick={() => {
                  if (flowStatus === 'running') {
                    setFlowStatus('stopped');
                  } else {
                    setDebugVisible(true);
                  }
                }}
                icon={
                  flowStatus === 'running' ? <BsPauseFill /> : <BsPlayFill />
                }
              />
            </Tooltip>

            <Tooltip title={formatMessage({ id: 'action.save' })}>
              <Button type="primary" onClick={saveFlow}>
                <FormattedMessage id="action.save" />
              </Button>
            </Tooltip>
          </Space>
        </StyledFlowToolbar>
      </StyledReactFlow>
      <Modal
        title={formatMessage({ id: 'flow.variable.query' })}
        open={debugVisible}
        onCancel={() => setDebugVisible(false)}
        onOk={debug}
        width={380}
        okText={formatMessage({ id: 'action.debug' })}
      >
        <br />
        <Form layout="vertical" form={debugForm} autoComplete="off">
          <Form.Item
            required
            name="query"
            rules={[
              {
                required: true,
                message: formatMessage({ id: 'flow.variable.query.required' }),
              },
            ]}
          >
            <Input.TextArea
              placeholder={formatMessage({ id: 'flow.variable.query' })}
            />
          </Form.Item>
        </Form>
      </Modal>
    </PageContainer>
  );
};
