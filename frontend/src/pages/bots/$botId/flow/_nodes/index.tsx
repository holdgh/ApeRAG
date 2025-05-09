import { ApeNode, ApeNodeType } from '@/types';
import {
  CaretDownOutlined,
  FunnelPlotOutlined,
  HomeOutlined,
  InteractionOutlined,
  MergeOutlined,
  ReadOutlined,
  WechatWorkOutlined,
} from '@ant-design/icons';
import { applyNodeChanges, Handle, NodeChange, Position } from '@xyflow/react';
import { useHover } from 'ahooks';
import { Button, Space, theme } from 'antd';
import { useCallback, useMemo, useRef } from 'react';
import { useIntl, useModel } from 'umi';
import { ApeNodeGlobal } from './_node_global';
import { ApeNodeKeywordSearch } from './_node_keyword_search';
import { ApeNodeLlm } from './_node_llm';
import { ApeNodeMerge } from './_node_merge';
import { ApeNodeRerank } from './_node_rerank';
import { ApeNodeVectorSearch } from './_node_vector_search';
import {
  StyledFlowNode,
  StyledFlowNodeAvatar,
  StyledFlowNodeBody,
  StyledFlowNodeContainer,
  StyledFlowNodeHeader,
  StyledFlowNodeLabel,
} from './_styles';

type NodeConfig = {
  [key in ApeNodeType]: {
    color: string;
    icon: React.ReactNode;
    content: React.ReactNode;
    label: React.ReactNode;
  };
};

const ApeBasicNode = (node: ApeNode) => {
  const { token } = theme.useToken();
  const { formatMessage } = useIntl();
  const { nodes, setNodes } = useModel('bots.$botId.flow.model');

  const nodeRef = useRef(null);
  const isHovering = useHover(nodeRef);

  const selected = useMemo(() => node.selected, [node]);
  const collapsed = useMemo(() => Boolean(node.data.collapsed), [node]);

  const NodeConfigs: NodeConfig = useMemo(
    () => ({
      global: {
        color: token.cyan,
        icon: <HomeOutlined />,
        content: <ApeNodeGlobal node={node} />,
        label: formatMessage({ id: 'flow.node.type.global' }),
      },
      vector_search: {
        color: token.orange,
        icon: <InteractionOutlined />,
        content: <ApeNodeVectorSearch node={node} />,
        label: formatMessage({ id: 'flow.node.type.vector_search' }),
      },
      keyword_search: {
        color: token.volcano,
        icon: <ReadOutlined />,
        content: <ApeNodeKeywordSearch node={node} />,
        label: formatMessage({ id: 'flow.node.type.keyword_search' }),
      },
      merge: {
        color: token.purple,
        icon: <MergeOutlined />,
        content: <ApeNodeMerge node={node} />,
        label: formatMessage({ id: 'flow.node.type.merge' }),
      },
      rerank: {
        color: token.magenta,
        icon: <FunnelPlotOutlined />,
        content: <ApeNodeRerank node={node} />,
        label: formatMessage({ id: 'flow.node.type.rerank' }),
      },
      llm: {
        color: token.blue,
        icon: <WechatWorkOutlined />,
        content: <ApeNodeLlm node={node} />,
        label: formatMessage({ id: 'flow.node.type.llm' }),
      },
    }),
    [node],
  );

  const nodeConfig = useMemo(
    () => NodeConfigs[node.type as ApeNodeType],
    [node],
  );

  const toggleCollapsed = useCallback(() => {
    const _node = nodes.find((n) => n.id === node.id);
    if (!_node) return;

    setNodes((nds) => {
      const changes: NodeChange[] = [
        {
          id: _node.id,
          type: 'replace',
          item: {
            ..._node,
            data: {
              ..._node.data,
              collapsed: !collapsed,
            },
          },
        },
      ];
      return applyNodeChanges(changes, nds);
    });
  }, [node]);

  return (
    <StyledFlowNodeContainer
      token={token}
      selected={selected}
      isHovering={isHovering}
      color={nodeConfig.color}
      ref={nodeRef}
    >
      <Handle type="target" position={node.targetPosition || Position.Left} />
      <StyledFlowNode className="drag-handle">
        <StyledFlowNodeHeader token={token}>
          <Space>
            <StyledFlowNodeAvatar
              token={token}
              color={nodeConfig.color}
              shape="square"
              src={nodeConfig.icon}
            />
            <StyledFlowNodeLabel>{nodeConfig.label}</StyledFlowNodeLabel>
          </Space>
          <Button
            type="text"
            icon={
              <CaretDownOutlined
                style={{
                  color: token.colorTextTertiary,
                  fontSize: '0.8em',
                  transform: `rotate(${collapsed ? -90 : 0}deg)`,
                  transitionDuration: '0.3s',
                }}
              />
            }
            onClick={toggleCollapsed}
          />
        </StyledFlowNodeHeader>
        <StyledFlowNodeBody collapsed={collapsed} token={token}>
          {nodeConfig.content}
        </StyledFlowNodeBody>
      </StyledFlowNode>

      <Handle
        className="node-handler-end"
        type="source"
        position={node.sourcePosition || Position.Right}
        onClick={(e) => {
          e.stopPropagation();
        }}
      />

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
  );
};

export const NodeTypes: { [key in ApeNodeType]: any } = {
  global: ApeBasicNode,
  vector_search: ApeBasicNode,
  keyword_search: ApeBasicNode,
  merge: ApeBasicNode,
  rerank: ApeBasicNode,
  llm: ApeBasicNode,
};
