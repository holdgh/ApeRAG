import { ApeNode, ApeNodeType } from '@/types';
import {
  CaretDownOutlined,
  EditOutlined,
  FunnelPlotOutlined,
  HomeOutlined,
  InteractionOutlined,
  MergeOutlined,
  ReadOutlined,
  WechatWorkOutlined,
} from '@ant-design/icons';
import { applyNodeChanges, Handle, NodeChange, Position } from '@xyflow/react';
import { useHover } from 'ahooks';
import { Button, ConfigProvider, Form, Input, Modal, Space, theme } from 'antd';
import { useCallback, useMemo, useRef, useState } from 'react';
import { useIntl, useModel } from 'umi';
import { ApeNodeKeywordSearch } from './_node_keyword_search';
import { ApeNodeLlm } from './_node_llm';
import { ApeNodeMerge } from './_node_merge';
import { ApeNodeRerank } from './_node_rerank';
import { ApeNodeStart } from './_node_start';
import { ApeNodeVectorSearch } from './_node_vector_search';

import {
  StyledFlowNode,
  StyledFlowNodeAvatar,
  StyledFlowNodeBody,
  StyledFlowNodeContainer,
  StyledFlowNodeHeader,
  StyledFlowNodeLabel,
} from './_styles';
const { darkAlgorithm, defaultAlgorithm } = theme;

import { CSS_PREFIX, THEME_TOKENS } from '@/constants';

type NodeConfig = {
  [key in ApeNodeType]: {
    color: string;
    icon: React.ReactNode;
    label: string;
    content?: React.ReactNode;
    width?: number;
    disableConnectionTarget?: boolean;
    disableConnectionSource?: boolean;
  };
};

const ApeBasicNode = (node: ApeNode) => {
  const [labelModalVisible, setLabelModalVisible] = useState<boolean>(false);

  const { nodes, setNodes } = useModel('bots.$botId.flow.model');
  const { themeName } = useModel('global');

  const algorithm = useMemo(
    () => (themeName.includes('dark') ? darkAlgorithm : defaultAlgorithm),
    [themeName],
  );

  const { token } = theme.useToken();
  const { formatMessage } = useIntl();
  const tokens = useMemo(
    () => ({ ...THEME_TOKENS[themeName], fontSize: 12 }),
    [themeName],
  );

  const [form] = Form.useForm<{ ariaLabel: string }>();

  const nodeRef = useRef(null);
  const isHovering = useHover(nodeRef);

  const selected = useMemo(() => node.selected, [node]);
  const collapsed = useMemo(() => Boolean(node.data.collapsed), [node]);
  const originNode = useMemo(() => nodes.find((n) => n.id === node.id), [node]);
  const configs = useMemo(
    (): NodeConfig => ({
      start: {
        color: token.cyan,
        icon: <HomeOutlined />,
        content: <ApeNodeStart />,
        label:
          originNode?.ariaLabel ||
          formatMessage({ id: 'flow.node.type.global' }),
        width: 320,
        disableConnectionTarget: true,
      },
      vector_search: {
        color: token.orange,
        icon: <InteractionOutlined />,
        content: <ApeNodeVectorSearch node={node} />,
        width: 360,
        label:
          originNode?.ariaLabel ||
          formatMessage({ id: 'flow.node.type.vector_search' }),
      },
      keyword_search: {
        color: token.volcano,
        icon: <ReadOutlined />,
        content: <ApeNodeKeywordSearch node={node} />,
        width: 360,
        label:
          originNode?.ariaLabel ||
          formatMessage({ id: 'flow.node.type.keyword_search' }),
      },
      merge: {
        color: token.purple,
        icon: <MergeOutlined />,
        content: <ApeNodeMerge node={node} />,
        label:
          originNode?.ariaLabel ||
          formatMessage({ id: 'flow.node.type.merge' }),
      },
      rerank: {
        color: token.magenta,
        icon: <FunnelPlotOutlined />,
        content: <ApeNodeRerank node={node} />,
        width: 260,
        label:
          originNode?.ariaLabel ||
          formatMessage({ id: 'flow.node.type.rerank' }),
      },
      llm: {
        color: token.blue,
        icon: <WechatWorkOutlined />,
        content: <ApeNodeLlm node={node} />,
        width: 320,
        label:
          originNode?.ariaLabel || formatMessage({ id: 'flow.node.type.llm' }),
        disableConnectionSource: true,
      },
    }),
    [node],
  );

  const config = useMemo(() => configs[node.type as ApeNodeType] || {}, [node]);

  const onToggleCollapsed = useCallback(() => {
    if (!originNode) return;
    setNodes((nds) => {
      const changes: NodeChange[] = [
        {
          id: originNode.id,
          type: 'replace',
          item: {
            ...originNode,
            data: {
              ...originNode.data,
              collapsed: !collapsed,
            },
          },
        },
      ];
      return applyNodeChanges(changes, nds);
    });
  }, [originNode]);

  const onEditNodeLable = useCallback(() => {
    form.setFieldValue('ariaLabel', config.label);
    setLabelModalVisible(true);
  }, [node]);

  const onEditNodeLableClose = useCallback(() => {
    setLabelModalVisible(false);
  }, [node]);

  const onSaveNodeLable = useCallback(async () => {
    if (!originNode) return;
    const { ariaLabel } = await form.validateFields();
    setNodes((nds) => {
      const changes: NodeChange[] = [
        {
          id: originNode.id,
          type: 'replace',
          item: {
            ...originNode,
            ariaLabel,
          },
        },
      ];
      return applyNodeChanges(changes, nds);
    });
    setLabelModalVisible(false);
  }, [node]);

  return (
    <>
      <StyledFlowNodeContainer
        token={token}
        selected={selected}
        isHovering={isHovering}
        color={config.color}
        ref={nodeRef}
      >
        {!config.disableConnectionTarget && (
          <Handle
            type="target"
            position={node.targetPosition || Position.Left}
          />
        )}

        <StyledFlowNode style={{ width: config.width }}>
          <StyledFlowNodeHeader token={token} className="drag-handle">
            <Space>
              <StyledFlowNodeAvatar
                token={token}
                color={config.color}
                shape="square"
                src={config.icon}
              />
              <StyledFlowNodeLabel>{config.label}</StyledFlowNodeLabel>
              {isHovering && (
                <Button
                  type="text"
                  onClick={onEditNodeLable}
                  icon={<EditOutlined />}
                />
              )}
            </Space>
            <Space>
              <Button
                type="text"
                onClick={onToggleCollapsed}
                icon={
                  <CaretDownOutlined
                    style={{
                      fontSize: '0.8em',
                      transform: `rotate(${collapsed ? -90 : 0}deg)`,
                      transitionDuration: '0.3s',
                    }}
                  />
                }
              />
            </Space>
          </StyledFlowNodeHeader>
          <StyledFlowNodeBody token={token} collapsed={collapsed}>
            <ConfigProvider
              prefixCls={CSS_PREFIX}
              theme={{
                algorithm,
                token: tokens,
              }}
            >
              {config.content}
            </ConfigProvider>
          </StyledFlowNodeBody>
        </StyledFlowNode>

        {!config.disableConnectionSource && (
          <Handle
            className="node-handler-end"
            type="source"
            position={node.sourcePosition || Position.Right}
            onClick={(e) => {
              e.stopPropagation();
            }}
          />
        )}

        {/* <NodeResizeControl
        style={{
          border: 'none',
          background: 'none',
          width: 16,
          height: 16,
          marginTop: -10,
          marginLeft: -8,
          color: token.colorBorder,
        }}
        minWidth={200}
        minHeight={48}
        maxWidth={600}
        maxHeight={300}
      >
        <BiFilter style={{ transform: 'rotate(-45deg)' }} />
      </NodeResizeControl> */}
      </StyledFlowNodeContainer>

      <Modal
        title={formatMessage({ id: 'flow.node.custom_label' })}
        open={labelModalVisible}
        onCancel={onEditNodeLableClose}
        onOk={onSaveNodeLable}
        width={380}
      >
        <br />
        <Form form={form} autoComplete="off">
          <Form.Item name="ariaLabel">
            <Input />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
};

export const NodeTypes: { [key in ApeNodeType]: any } = {
  start: ApeBasicNode,
  vector_search: ApeBasicNode,
  keyword_search: ApeBasicNode,
  merge: ApeBasicNode,
  rerank: ApeBasicNode,
  llm: ApeBasicNode,
};
