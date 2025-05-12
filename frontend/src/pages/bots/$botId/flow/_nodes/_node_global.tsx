import { ApeNode, ApeNodeVars } from '@/types';
import {
  CaretRightOutlined,
  DeleteOutlined,
  PlusOutlined,
  QuestionCircleOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import {
  Button,
  Collapse,
  Space,
  Table,
  TableProps,
  Tag,
  theme,
  Tooltip,
  Typography,
} from 'antd';
import { FormattedMessage, useIntl } from 'umi';
import { getCollapsePanelStyle } from './_styles';

export const ApeNodeGlobal = ({ node }: { node: ApeNode }) => {
  const { token } = theme.useToken();
  const { formatMessage } = useIntl();

  const columns: TableProps<ApeNodeVars>['columns'] = [
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
    {
      title: formatMessage({ id: 'action.name' }),
      width: 60,
      render: (value, record) => {
        return (
          <Space>
            <Button
              disabled={record.name === 'query'}
              type="text"
              size="small"
              icon={<SettingOutlined />}
            />
            <Button
              disabled={record.name === 'query'}
              type="text"
              size="small"
              icon={<DeleteOutlined />}
            />
          </Space>
        );
      },
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
          extra: (
            <Tooltip title={<FormattedMessage id="action.add" />}>
              <Button
                disabled
                type="link"
                size="small"
                icon={<PlusOutlined />}
              />
            </Tooltip>
          ),
          children: (
            <Table
              rowKey="name"
              pagination={false}
              size="small"
              bordered
              columns={columns}
              dataSource={node.data.vars}
            />
          ),
        },
      ]}
    />
  );
};
