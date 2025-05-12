import { ApeNode, ApeNodeVars } from '@/types';
import {
  CaretRightOutlined,
  DeleteOutlined,
  PlusOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import {
  Button,
  Collapse,
  Space,
  Table,
  TableProps,
  theme,
  Tooltip,
} from 'antd';
import { useMemo } from 'react';
import { FormattedMessage, useIntl, useModel } from 'umi';
import { getCollapsePanelStyle } from './_styles';

export const ApeNodeKeywordSearch = ({ node }: { node: ApeNode }) => {
  const { token } = theme.useToken();
  const { nodes } = useModel('bots.$botId.flow.model');
  const { formatMessage } = useIntl();

  const originNode = useMemo(() => nodes.find((n) => n.id === node.id), [node]);

  const columns: TableProps<ApeNodeVars>['columns'] = [
    {
      title: formatMessage({ id: 'flow.variable.title' }),
      dataIndex: 'name',
    },
    {
      title: formatMessage({ id: 'flow.variable.source_type' }),
      dataIndex: 'source_type',
    },
    {
      title: formatMessage({ id: 'flow.variable.value' }),
      dataIndex: 'global_var',
    },
    {
      title: formatMessage({ id: 'action.name' }),
      width: 60,
      render: () => {
        return (
          <Space>
            <Button type="text" size="small" icon={<SettingOutlined />} />
            <Button type="text" size="small" icon={<DeleteOutlined />} />
          </Space>
        );
      },
    },
  ];
  const records = originNode?.data.vars || [];

  const onAddParams: React.MouseEventHandler<HTMLElement> = (e) => {
    e.stopPropagation();
  };

  return (
    <>
      <Collapse
        bordered={false}
        expandIcon={({ isActive }) => {
          return <CaretRightOutlined rotate={isActive ? 90 : 0} />;
        }}
        size="middle"
        defaultActiveKey={['1']}
        style={{ background: 'none' }}
        items={[
          {
            key: '1',
            label: formatMessage({ id: 'flow.input.params' }),
            style: getCollapsePanelStyle(token),
            extra: (
              <Tooltip title={<FormattedMessage id="action.add" />}>
                <Button
                  type="link"
                  size="small"
                  icon={<PlusOutlined />}
                  onClick={onAddParams}
                />
              </Tooltip>
            ),
            children: (
              <Table
                rowKey="name"
                bordered
                size="small"
                pagination={false}
                columns={columns}
                dataSource={records}
                style={{ background: token.colorBgContainer }}
              />
            ),
          },
        ]}
      />
    </>
  );
};
