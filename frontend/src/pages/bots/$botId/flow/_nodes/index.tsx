import { ApeNode, ApeNodeConfig, ApeNodeType } from '@/types';
import {
  CaretDownOutlined,
  EditOutlined,
  LoadingOutlined,
} from '@ant-design/icons';
import { applyNodeChanges, Handle, NodeChange, Position } from '@xyflow/react';
import { useHover } from 'ahooks';
import { Button, Form, Input, Modal, Space, theme } from 'antd';
import React, { useCallback, useMemo, useRef, useState } from 'react';
import { useIntl, useModel } from 'umi';
import {
  StyledFlowNode,
  StyledFlowNodeAvatar,
  StyledFlowNodeBody,
  StyledFlowNodeContainer,
  StyledFlowNodeHeader,
  StyledFlowNodeLabel,
} from './_styles';

const ApeBasicNode = (node: ApeNode) => {
  const [labelModalVisible, setLabelModalVisible] = useState<boolean>(false);
  const { nodes, setNodes, getNodeConfig } = useModel('bots.$botId.flow.model');
  const { token } = theme.useToken();
  const { formatMessage } = useIntl();
  const [form] = Form.useForm<{ ariaLabel: string }>();

  const nodeRef = useRef(null);
  const isHovering = useHover(nodeRef);
  const selected = useMemo(() => node.selected, [node]);
  const collapsed = useMemo(() => Boolean(node.data.collapsed), [node]);
  const running = useMemo(() => Boolean(node?.data.running), [node]);

  const originNode = useMemo(() => nodes.find((n) => n.id === node.id), [node]);
  const config: ApeNodeConfig = useMemo(
    () =>
      getNodeConfig(
        originNode?.type as ApeNodeType,
        originNode?.ariaLabel ||
          formatMessage({ id: `flow.node.type.${originNode?.type}` }),
      ),
    [originNode],
  );

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
  }, []);

  const onEditNodeLableClose = useCallback(() => {
    setLabelModalVisible(false);
  }, []);

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
  }, [originNode]);

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
                src={running ? <LoadingOutlined /> : config.icon}
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
            {config.content &&
              originNode &&
              React.createElement(config.content, { node: originNode })}
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
