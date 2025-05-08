import { ApeNode, ApeNodeType } from '@/types/flow';
import { HomeOutlined, WechatWorkOutlined } from '@ant-design/icons';
import { Handle, NodeResizeControl, Position } from '@xyflow/react';
import { useHover } from 'ahooks';
import { GlobalToken, Space, theme, Typography } from 'antd';
import { useMemo, useRef } from 'react';
import { BiFilter } from 'react-icons/bi';
import { css, styled, useIntl } from 'umi';

type NodeTypeConfig = {
  [key in ApeNodeType]: {
    icon?: React.ReactNode;
    color?: string;
  };
};

export const StyledFlowNode = styled('div').withConfig({
  shouldForwardProp: (prop) =>
    !['token', 'color', 'selected', 'isHovering'].includes(prop),
})<{
  token: GlobalToken;
  color?: string;
  selected?: boolean;
  isHovering?: boolean;
}>`
  ${({ selected, token, color, isHovering = false }) => {
    return css`
      border-radius: 6px;
      color: ${token.colorText};
      border-color: ${selected ? color : token.colorBorder};
      border-left-color: ${color};
      border-width: 1px;
      border-left-width: 5px;
      border-style: solid;
      border-left-style: solid;
      background: ${token.colorBgContainer};
      height: 100%;
      min-width: 200px;
      min-height: 40px;
      padding: 12px;
      transition:
        border-color 0.3s,
        box-shadow 0.3s;
      box-shadow: ${token.boxShadow};
      z-index: ${isHovering || selected ? 1 : 0};
      .react-flow__handle {
        width: 9px;
        height: 9px;
        border-radius: 9px;
        transition:
          border-color 0.3s,
          background 0.3s,
          width 0.3s,
          height 0.3s;
        border-width: 1px;
        background: ${token.colorBgContainer};
        border-color: ${selected ? color : token.colorBorder};
        &.node-handler-end {
          cursor: pointer;
          &:after {
            transition: all 0.3s;
            text-align: center;
            display: block;
            content: '+';
            line-height: 0;
            opacity: 0;
            color: ${token.colorWhite};
            transform: translate(0px, 2px);
          }
        }
      }

      &:hover {
        box-shadow: ${token.boxShadow};
        border-color: ${color};
        .react-flow__handle {
          border-color: ${color};
        }
        .node-handler-end {
          width: 18px;
          height: 18px;
          background-color: ${color};
          &:after {
            font-size: 14px;
            opacity: 1;
            transform: translate(0px, 7px);
          }
        }
      }
    `;
  }}
`;

export const ApeFlowNode = (node: ApeNode) => {
  const { token } = theme.useToken();
  const { formatMessage } = useIntl();
  const { selected } = node;
  const nodeType = (node.type || 'normal') as ApeNodeType;

  const nodeRef = useRef(null);
  const isHovering = useHover(nodeRef);

  const nodeTypeConfig: NodeTypeConfig = useMemo(
    () => ({
      global: {
        icon: <HomeOutlined />,
        color: token.colorPrimary,
      },
      keyword_search: {
        icon: <WechatWorkOutlined />,
        color: token.colorPrimary,
      },
      vector_search: {
        color: token.red,
      },
      merge: {
        color: token.red,
      },
      rerank: {
        color: token.red,
      },
      llm: {
        color: token.red,
      },
    }),
    [token],
  );

  return (
    <StyledFlowNode
      token={token}
      selected={selected}
      isHovering={isHovering}
      color={nodeTypeConfig[nodeType]?.color}
      ref={nodeRef}
    >
      <Handle type="target" position={node.targetPosition || Position.Left} />

      <Space>
        {nodeTypeConfig[nodeType]?.icon}
        <Typography.Text>{nodeType}</Typography.Text>
      </Space>

      <Handle
        className="node-handler-end"
        type="source"
        position={node.sourcePosition || Position.Right}
        onClick={(e) => {
          e.stopPropagation();
        }}
      />

      <NodeResizeControl
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
      </NodeResizeControl>
    </StyledFlowNode>
  );
};
