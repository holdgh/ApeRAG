import { CloseOutlined } from '@ant-design/icons';
import { applyNodeChanges, NodeChange } from '@xyflow/react';
import { Button, Card, GlobalToken, theme, Tooltip } from 'antd';
import alpha from 'color-alpha';
import { useCallback, useMemo } from 'react';
import { css, FormattedMessage, styled, useIntl, useModel } from 'umi';
import { v4 as uuidV4 } from 'uuid';

export const StyledFlowNodeDetail = styled(Card).withConfig({
  shouldForwardProp: (prop) => !['visible', 'token'].includes(prop),
})<{ visible: boolean; token: GlobalToken }>`
  ${({ visible, token }) => {
    return css`
      position: absolute;
      right: ${visible ? 15 : -500}px;
      top: 70px;
      bottom: 20px;
      width: 415px;
      display: flex;
      flex-direction: column;
      transition: right 0.3s;
      background: ${alpha(token.colorBgContainer, 0.5)};
      backdrop-filter: blur(10px);
      z-index: 5;
      > ul:last-child {
        display: flex;
        padding: ${token.paddingSM}px;
        justify-content: flex-end;
        background: none;
        > li {
          width: auto !important;
          margin: 0;
        }
      }
    `;
  }}
`;

export const ApeFlowNodeDetail = () => {
  const { token } = theme.useToken();
  const { setNodes, nodes } = useModel('flow');
  const { formatMessage } = useIntl();

  const node = useMemo(() => {
    const selectedNodes = nodes.filter((n) => n.selected);
    if (selectedNodes.length === 1) return selectedNodes[0];
  }, [nodes]);

  const onSave = useCallback(() => {
    if (!node) return;
    const formData = {
      label: uuidV4(),
    };
    setNodes((nds) => {
      const changes: NodeChange[] = [
        {
          id: node.id,
          type: 'replace',
          item: {
            ...node,
            data: {
              ...node.data,
              ...formData,
            },
          },
        },
      ];
      return applyNodeChanges(changes, nds);
    });
  }, [node]);

  const onClose = useCallback(() => {
    if (!node) return;

    setNodes((nds) => {
      const changes: NodeChange[] = nds
        .filter((n) => n.selected)
        .map((n) => ({
          id: n.id,
          type: 'replace',
          item: {
            ...n,
            selected: false,
          },
        }));
      return applyNodeChanges(changes, nds);
    });
  }, [node]);

  return (
    <StyledFlowNodeDetail
      token={token}
      visible={Boolean(node)}
      title={node?.data.label}
      size="small"
      actions={[
        <Tooltip key="update" title={formatMessage({ id: 'action.update' })}>
          <Button type="primary" onClick={onSave}>
            <FormattedMessage id="action.update" />
          </Button>
        </Tooltip>,
      ]}
      extra={
        <Tooltip key="update" title={formatMessage({ id: 'action.close' })}>
          <Button
            type="text"
            icon={<CloseOutlined />}
            onClick={() => onClose()}
          />
        </Tooltip>
      }
      styles={{
        header: {
          flex: 'none',
          padding: token.paddingSM,
        },
        body: {
          flex: 'auto',
          overflow: 'auto',
          padding: token.paddingSM,
        },
      }}
    >
      node config
    </StyledFlowNodeDetail>
  );
};
