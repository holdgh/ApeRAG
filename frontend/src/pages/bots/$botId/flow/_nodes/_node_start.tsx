import { ApeNodeVar } from '@/types';
import { CaretRightOutlined, QuestionCircleOutlined } from '@ant-design/icons';
import {
  Collapse,
  Space,
  Table,
  TableProps,
  Tag,
  theme,
  Tooltip,
  Typography,
} from 'antd';
import { useIntl, useModel } from 'umi';
import { getCollapsePanelStyle } from './_styles';

export const ApeNodeStart = () => {
  const { globalVariables } = useModel('bots.$botId.flow.model');
  const { token } = theme.useToken();
  const { formatMessage } = useIntl();

  const columns: TableProps<ApeNodeVar>['columns'] = [
    {
      title: formatMessage({ id: 'flow.variable.title' }),
      dataIndex: 'name',
      render: (value, record) => {
        return (
          <Space>
            <Typography.Text>{value}</Typography.Text>
            {record.description && (
              <Tooltip title={record.description}>
                <Typography.Text type="secondary">
                  <QuestionCircleOutlined />
                </Typography.Text>
              </Tooltip>
            )}
          </Space>
        );
      },
    },
    {
      title: formatMessage({ id: 'flow.variable.type' }),
      dataIndex: 'type',
      render: (value) => <Tag color={token.colorPrimary}>{value}</Tag>,
    },
  ];

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
          label: formatMessage({ id: 'flow.variable.global' }),
          style: getCollapsePanelStyle(token),
          children: (
            <Table
              rowKey="name"
              pagination={false}
              size="small"
              bordered
              columns={columns}
              dataSource={globalVariables}
            />
          ),
        },
      ]}
    />
  );
};
