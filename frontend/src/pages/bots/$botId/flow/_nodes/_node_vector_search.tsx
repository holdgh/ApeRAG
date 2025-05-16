import { ApeNode } from '@/types';
import { CaretRightOutlined } from '@ant-design/icons';
import { Collapse, Form, Select, Slider, Table, theme } from 'antd';
import { useCallback, useEffect } from 'react';
import { useIntl, useModel } from 'umi';
import { getCollapsePanelStyle } from './_styles';

type VarType = {
  top_k: number;
  similarity_threshold: number;
  collection_ids: string[];
};

export const ApeNodeVectorSearch = ({ node }: { node: ApeNode }) => {
  const { token } = theme.useToken();
  const [form] = Form.useForm<VarType>();
  const { getNodeOutputVars } = useModel('bots.$botId.flow.model');
  const { formatMessage } = useIntl();
  const { collections } = useModel('collection');

  /**
   * on node form change
   */
  const onValuesChange = useCallback(
    (changedValues: VarType) => {
      if (!node) return;
      const vars = node?.data.vars;
      const varTopK = vars?.find((item) => item.name === 'top_k');
      const varSimilarityThreshold = vars?.find(
        (item) => item.name === 'similarity_threshold',
      );
      const varCollectionIds = vars?.find(
        (item) => item.name === 'collection_ids',
      );
      if (varTopK && changedValues.top_k !== undefined) {
        varTopK.value = changedValues.top_k;
      }
      if (
        varSimilarityThreshold &&
        changedValues.similarity_threshold !== undefined
      ) {
        varSimilarityThreshold.value = changedValues.similarity_threshold;
      }

      if (varCollectionIds && changedValues.collection_ids) {
        varCollectionIds.value = changedValues.collection_ids;
      }
    },
    [node],
  );

  /**
   * init node form data
   */
  useEffect(() => {
    const vars = node?.data.vars;
    const top_k = Number(
      vars?.find((item) => item.name === 'top_k')?.value || 5,
    );
    const similarity_threshold = Number(
      vars?.find((item) => item.name === 'similarity_threshold')?.value || 0.2,
    );
    const collection_ids =
      vars?.find((item) => item.name === 'collection_ids')?.value || [];
    form.setFieldsValue({ top_k, similarity_threshold, collection_ids });
  }, []);

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
                  >
                    <Select
                      variant="filled"
                      mode="multiple"
                      suffixIcon={null}
                      options={collections?.map((collection) => ({
                        label: collection.title,
                        value: collection.id,
                      }))}
                    />
                  </Form.Item>
                  <Form.Item
                    required
                    label={formatMessage({ id: 'flow.top_k' })}
                    name="top_k"
                    tooltip={formatMessage({ id: 'flow.top_k.tips' })}
                  >
                    <Slider style={{ margin: 0 }} min={1} max={10} step={1} />
                  </Form.Item>
                  <Form.Item
                    required
                    style={{ marginBottom: 0 }}
                    label={formatMessage({ id: 'flow.similarity_threshold' })}
                    name="similarity_threshold"
                    tooltip={formatMessage({
                      id: 'flow.similarity_threshold.tips',
                    })}
                  >
                    <Slider style={{ margin: 0 }} min={0} max={1} step={0.01} />
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
                columns={[
                  {
                    title: formatMessage({ id: 'flow.variable.source_type' }),
                    dataIndex: 'source_type',
                  },
                  {
                    title: formatMessage({ id: 'flow.variable.title' }),
                    dataIndex: 'global_var',
                  },
                ]}
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
