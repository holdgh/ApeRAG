import { ApeNode, ApeNodeVars } from '@/types';
import Icon, {
  DeleteOutlined,
  QuestionCircleOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import {
  Button,
  Space,
  Table,
  TableProps,
  Tag,
  theme,
  Tooltip,
  Typography,
} from 'antd';
import { TbVariable } from 'react-icons/tb';
import { FormattedMessage, useIntl } from 'umi';

export const ApeNodeGlobal = ({ node }: { node: ApeNode }) => {
  const { token } = theme.useToken();
  const { formatMessage } = useIntl();

  const columns: TableProps<ApeNodeVars>['columns'] = [
    {
      title: (
        <div style={{ fontSize: 12 }}>
          {formatMessage({ id: 'flow.variable.title' })}
        </div>
      ),
      dataIndex: 'name',
      render: (value, record) => {
        return (
          <Space>
            <Typography.Text style={{ fontSize: 12 }}>{value}</Typography.Text>
            {record.description && (
              <Tooltip title={record.description}>
                <Typography.Text style={{ fontSize: 12 }} type="secondary">
                  <QuestionCircleOutlined />
                </Typography.Text>
              </Tooltip>
            )}
          </Space>
        );
      },
    },
    {
      title: (
        <div style={{ fontSize: 12 }}>
          {formatMessage({ id: 'flow.variable.type' })}
        </div>
      ),
      dataIndex: 'type',
      render: (value) => <Tag color={token.colorPrimary}>{value}</Tag>,
    },
    {
      title: (
        <div style={{ fontSize: 12 }}>
          {formatMessage({ id: 'action.name' })}
        </div>
      ),
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
    <>
      <Space
        style={{
          display: 'flex',
          marginBottom: 8,
          justifyContent: 'space-between',
        }}
      >
        <Space>
          <Icon viewBox="0 0 14 14" style={{ color: token.blue }}>
            <TbVariable />
          </Icon>
          <Typography>全局变量</Typography>
        </Space>
        <Button disabled type="text" size="small" style={{ fontSize: 12 }}>
          <FormattedMessage id="action.add" />
        </Button>
      </Space>
      <Table
        rowKey="name"
        pagination={false}
        size="small"
        bordered
        columns={columns}
        dataSource={node.data.vars}
      />
    </>
  );
};
