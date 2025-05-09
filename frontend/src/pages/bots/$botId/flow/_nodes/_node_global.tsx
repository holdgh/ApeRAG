import { ApeNode } from '@/types';
import { HomeOutlined } from '@ant-design/icons';
import { Handle, NodeResizeControl, Position } from '@xyflow/react';
import { useHover } from 'ahooks';
import { Space, theme, Typography } from 'antd';
import { useRef } from 'react';
import { BiFilter } from 'react-icons/bi';
import { FormattedMessage } from 'umi';

import { StyledFlowNode, StyledFlowNodeAvatar } from './_styles';

export const ApeNodeGlobal = (node: ApeNode) => {
  const { token } = theme.useToken();
  // const { formatMessage } = useIntl();
  const { selected } = node;

  const nodeRef = useRef(null);
  const isHovering = useHover(nodeRef);

  return (
    <StyledFlowNode
      token={token}
      selected={selected}
      isHovering={isHovering}
      color={token.cyan}
      ref={nodeRef}
    >
      <Handle type="target" position={node.targetPosition || Position.Left} />

      <Space>
        <StyledFlowNodeAvatar
          token={token}
          color={token.cyan}
          shape="square"
          src={<HomeOutlined />}
        />
        <Typography.Text>
          <FormattedMessage id={`flow.node.type.global`} />
        </Typography.Text>
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
