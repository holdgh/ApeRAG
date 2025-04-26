import { ApeNode, ApeNodeType } from '@/types/flow';
import {
  ArrowRightOutlined,
  HomeOutlined,
  WechatWorkOutlined,
} from '@ant-design/icons';
import {
  applyNodeChanges,
  getConnectedEdges,
  getIncomers,
  getOutgoers,
  Handle,
  NodeResizeControl,
  Position,
} from '@xyflow/react';
import { useHover } from 'ahooks';
import {
  Button,
  Divider,
  Dropdown,
  GetProp,
  GlobalToken,
  Menu,
  MenuProps,
  Space,
  theme,
  Tooltip,
  Typography,
} from 'antd';
import _ from 'lodash';
import { useCallback, useMemo, useRef } from 'react';
import { BiFilter } from 'react-icons/bi';
import { BsCaretRight, BsGear, BsTrash } from 'react-icons/bs';
import { css, styled, useIntl, useModel } from 'umi';

type NodeTypeConfig = {
  [key in ApeNodeType]: {
    icon?: React.ReactNode;
    color?: string;
  };
};

type MenuItem = GetProp<MenuProps, 'items'>[number];

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
            transform: translate(0px, 1px);
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
            transform: translate(0px, 6px);
          }
        }
      }
    `;
  }}
`;

export const StyledFlowNodeToolbar = styled('div').withConfig({
  shouldForwardProp: (prop) => !['token', 'isVisible'].includes(prop),
})<{
  token: GlobalToken;
  isVisible: boolean;
}>`
  ${({ token, isVisible }) => {
    return css`
      border-radius: 4px;
      border: 1px solid ${token.colorBorderSecondary};
      padding: 4px;
      background: ${token.colorBgContainer};
      position: absolute;
      right: 0;
      top: ${isVisible ? -36 : 0}px;
      opacity: ${isVisible ? 1 : 0};
      transition: all 0.3s;
      z-index: -1;
    `;
  }}
`;

export const ApeFlowNode = (node: ApeNode) => {
  const { token } = theme.useToken();
  const { formatMessage } = useIntl();
  const { setNodes, setEdges, nodes, edges, edgeType, getEdgeId } =
    useModel('flow');
  const { models } = useModel('models');
  const { data, selected } = node;
  const nodeType = (node.type || 'normal') as ApeNodeType;

  const nodeRef = useRef(null);
  const isHovering = useHover(nodeRef);

  const groupModels: MenuItem[] = useMemo(
    () =>
      Object.keys(_.groupBy(models, 'family_name')).map(
        (familyName, fIndex) => {
          const children = models?.filter(
            (item) => item.family_name === familyName,
          );
          return {
            label: children?.[0]?.family_label,
            key: fIndex,
            type: 'group',
            children: children?.map((item, cIndex) => ({
              ...item,
              key: `${fIndex}-${cIndex}`,
            })),
          };
        },
      ),
    [models],
  );

  const onNodeDelete = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      if (!node.deletable) return;
      setNodes((nds) =>
        applyNodeChanges([{ id: node.id, type: 'remove' }], nds),
      );
      setEdges(
        [node].reduce((acc, nd) => {
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

  const onNodeEdit = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
    },
    [node],
  );

  const onNodeDebug = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
    },
    [node],
  );

  const nodeTypeConfig: NodeTypeConfig = useMemo(
    () => ({
      start: {
        icon: <HomeOutlined />,
        color: token.colorPrimary,
      },
      end: {
        icon: <WechatWorkOutlined />,
        color: token.colorPrimary,
      },
      normal: {
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
      color={nodeTypeConfig[nodeType].color}
      ref={nodeRef}
    >
      {nodeType !== 'start' && (
        <Handle type="target" position={node.targetPosition || Position.Left} />
      )}

      <StyledFlowNodeToolbar isVisible={selected || isHovering} token={token}>
        <Space split={<Divider type="vertical" style={{ margin: 0 }} />}>
          <Tooltip title={formatMessage({ id: 'action.settings' })}>
            <Button
              size="small"
              type="text"
              icon={<BsGear />}
              onClick={onNodeEdit}
            />
          </Tooltip>
          <Tooltip title={formatMessage({ id: 'action.debug' })}>
            <Button
              size="small"
              type="text"
              onClick={onNodeDebug}
              icon={<BsCaretRight />}
            />
          </Tooltip>
          <Tooltip title={formatMessage({ id: 'action.delete' })}>
            <Button
              size="small"
              type="text"
              icon={<BsTrash />}
              onClick={onNodeDelete}
              disabled={!node.deletable}
            />
          </Tooltip>
        </Space>
      </StyledFlowNodeToolbar>

      <Space>
        {nodeTypeConfig[nodeType].icon}
        <Typography.Text>{data.label}</Typography.Text>
      </Space>

      {nodeType !== 'end' && (
        <Dropdown
          trigger={['click']}
          getPopupContainer={() => nodeRef.current || document.body}
          overlayStyle={{
            boxShadow: 'none',
            left: '100%',
            marginLeft: 12,
            top: 0,
          }}
          dropdownRender={() => (
            <div
              onWheel={(e) => e.stopPropagation()}
              style={{
                minWidth: 200,
                maxHeight: 400,
                overflow: 'auto',
                border: `1px solid ${token.colorBorder}`,
                borderRadius: token.borderRadius,
                background: token.colorBgContainer,
              }}
            >
              <Menu
                style={{ padding: 0, background: 'none' }}
                expandIcon={
                  <ArrowRightOutlined
                    style={{
                      marginTop: 4,
                      transform: 'scale(0.8)',
                      opacity: 0.5,
                    }}
                  />
                }
                items={groupModels}
              />
            </div>
          )}
        >
          <Tooltip title={formatMessage({ id: 'flow.node.add' })}>
            <Handle
              className="node-handler-end"
              type="source"
              position={node.sourcePosition || Position.Right}
              onClick={(e) => {
                e.stopPropagation();
              }}
            />
          </Tooltip>
        </Dropdown>
      )}
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
