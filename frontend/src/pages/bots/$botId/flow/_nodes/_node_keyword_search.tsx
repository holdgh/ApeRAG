import { ApeNode, ApeNodeVar } from '@/types';
import { CaretRightOutlined } from '@ant-design/icons';
import { Collapse, Form, Select, Table, TableProps, theme } from 'antd';

import { useEffect, useMemo } from 'react';
import { useIntl, useModel } from 'umi';
import { getCollapsePanelStyle } from './_styles';

type VarType = {
  collection_ids: string[];
};

export const ApeNodeKeywordSearch = ({ node }: { node: ApeNode }) => {
  const { token } = theme.useToken();
  const { collections } = useModel('collection');
  const { getNodeOutputVars, nodes } = useModel('bots.$botId.flow.model');
  const { formatMessage } = useIntl();
  const originNode = useMemo(() => nodes.find((n) => n.id === node.id), [node]);
  const [form] = Form.useForm<VarType>();

  const columns: TableProps<ApeNodeVar>['columns'] = [
    {
      title: formatMessage({ id: 'flow.variable.source_type' }),
      dataIndex: 'source_type',
    },
    {
      title: formatMessage({ id: 'flow.variable.title' }),
      dataIndex: 'global_var',
    },
  ];

  const onValuesChange = (changedValues: VarType) => {
    if (!originNode) return;

    const vars = originNode?.data.vars;
    const varCollectionIds = vars?.find(
      (item) => item.name === 'collection_ids',
    );
    if (varCollectionIds && changedValues.collection_ids) {
      varCollectionIds.value = changedValues.collection_ids;
    }
  };

  useEffect(() => {
    const vars = originNode?.data.vars;
    const collection_ids =
      vars?.find((item) => item.name === 'collection_ids')?.value || [];
    form.setFieldsValue({ collection_ids });
  }, [originNode]);

  return (
    <>
      <Collapse
        bordered={false}
        expandIcon={({ isActive }) => {
          return <CaretRightOutlined rotate={isActive ? 90 : 0} />;
        }}
        size="middle"
        defaultActiveKey={['1', '2']}
        style={{ background: 'none' }}
        items={[
          {
            key: '1',
            label: formatMessage({ id: 'flow.search.params' }),
            style: getCollapsePanelStyle(token),
            children: (
              <>
                <Form
                  form={form}
                  layout="vertical"
                  onValuesChange={onValuesChange}
                  autoComplete="off"
                >
                  <Form.Item
                    required
                    label={formatMessage({ id: 'collection.name' })}
                    name="collection_ids"
                    style={{ marginBottom: 0 }}
                  >
                    <Select
                      variant="filled"
                      mode="multiple"
                      options={collections?.map((collection) => ({
                        label: collection.title,
                        value: collection.id,
                      }))}
                    />
                  </Form.Item>
                </Form>
              </>
            ),
          },
          {
            key: '2',
            label: formatMessage({ id: 'flow.input.params' }),
            style: getCollapsePanelStyle(token),
            children: (
              <Table
                rowKey="name"
                bordered
                size="small"
                pagination={false}
                columns={columns}
                dataSource={getNodeOutputVars(node)}
                style={{ background: token.colorBgContainer }}
              />
            ),
          },
        ]}
      />
    </>
  );
};
