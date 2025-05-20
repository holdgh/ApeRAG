import { Table, theme } from 'antd';
import { useIntl, useModel } from 'umi';

export const GlobalVars = () => {
  const { token } = theme.useToken();
  const { globalVariables } = useModel('bots.$botId.flow.model');
  const { formatMessage } = useIntl();
  return (
    <Table
      rowKey="name"
      bordered
      size="small"
      pagination={false}
      columns={[
        {
          title: formatMessage({ id: 'flow.variable.title' }),
          dataIndex: 'name',
        },
        {
          title: formatMessage({ id: 'flow.variable.type' }),
          dataIndex: 'type',
        },
        {
          title: formatMessage({ id: 'flow.variable.source_type' }),
          render: () => formatMessage({ id: 'flow.variable.global' }),
        },
      ]}
      dataSource={globalVariables}
      style={{ background: token.colorBgContainer }}
    />
  );
};
