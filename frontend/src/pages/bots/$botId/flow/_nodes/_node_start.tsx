import { CaretRightOutlined } from '@ant-design/icons';
import {
  Collapse,
  Space,
  Table,
  TableProps,
  Tag,
  theme,
  Typography,
} from 'antd';
import { useMemo } from 'react';
import { useIntl } from 'umi';
import { getCollapsePanelStyle } from './_styles';
import { ApeNode } from '@/types';

export const ApeNodeStart = ({ node }: { node: ApeNode }) => {
  const { token } = theme.useToken();
  const { formatMessage } = useIntl();

  const dataSource = [
    {
      name: 'query',
      type: 'string',
    },
  ];

  const columns: TableProps<{ name: string; type: string }>['columns'] =
    useMemo(
      () => [
        {
          title: formatMessage({ id: 'flow.variable.title' }),
          dataIndex: 'name',
          render: (value) => {
            return (
              <Space>
                <Typography.Text>{value}</Typography.Text>
              </Space>
            );
          },
        },
        {
          title: formatMessage({ id: 'flow.variable.type' }),
          dataIndex: 'type',
          render: (value) => <Tag color={token.colorPrimary}>{value}</Tag>,
        },
      ],
      [],
    );

  return (
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
          children: (
            <Table
              rowKey="name"
              pagination={false}
              size="small"
              bordered
              columns={columns}
              dataSource={dataSource}
            />
          ),
        },
        {
          key: '2',
          label: formatMessage({ id: 'flow.output.params' }),
          style: getCollapsePanelStyle(token),
          children: (
            <Table
              rowKey="name"
              pagination={false}
              size="small"
              bordered
              columns={columns}
              dataSource={dataSource}
            />
          ),
        },
      ]}
    />
  );
};
