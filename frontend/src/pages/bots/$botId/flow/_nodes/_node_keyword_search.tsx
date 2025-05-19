import { ApeNode } from '@/types';
import { CaretRightOutlined } from '@ant-design/icons';
import { Collapse, Form, Select, Table, theme } from 'antd';

import { applyNodeChanges, NodeChange } from '@xyflow/react';
import { useCallback, useEffect, useMemo } from 'react';
import { useIntl, useModel } from 'umi';
import { getCollapsePanelStyle } from './_styles';

export const ApeNodeKeywordSearch = ({ node }: { node: ApeNode }) => {
  const { token } = theme.useToken();
  const { collections } = useModel('collection');
  const { getNodeGlobalVars, setNodes } = useModel('bots.$botId.flow.model');
  const { formatMessage } = useIntl();

  const applyChanges = useCallback(() => {
    setNodes((nds) => {
      const changes: NodeChange[] = [
        { id: node.id, type: 'replace', item: node },
      ];
      return applyNodeChanges(changes, nds);
    });
  }, [node]);

  const getVarByName = useCallback(
    (name: string) => {
      return node.data.vars?.find((item) => item.name === name);
    },
    [node],
  );

  const [varCollectionIds, varQuery] = useMemo(
    () => [getVarByName('collection_ids'), getVarByName('query')],
    [getVarByName],
  );

  useEffect(() => {
    const vars = node.data.vars || [];
    if (!varCollectionIds) {
      vars?.push({
        name: 'collection_ids',
        value: [],
      });
    }
    if (!varQuery) {
      vars?.push({
        name: 'query',
        source_type: 'global',
        global_var: 'query',
      });
    }
    node.data.vars = vars;
    applyChanges();
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
                <Form layout="vertical" autoComplete="off">
                  <Form.Item
                    required
                    label={formatMessage({ id: 'collection.name' })}
                    style={{ marginBottom: 0 }}
                  >
                    <Select
                      variant="filled"
                      mode="multiple"
                      suffixIcon={null}
                      options={collections?.map((collection) => ({
                        label: collection.title,
                        value: collection.id,
                      }))}
                      value={varCollectionIds?.value}
                      onChange={(value) => {
                        if (varCollectionIds) {
                          varCollectionIds.value = value;
                        }
                        applyChanges();
                      }}
                      placeholder={formatMessage({ id: 'collection.select' })}
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
                dataSource={getNodeGlobalVars(node)}
                style={{ background: token.colorBgContainer }}
              />
            ),
          },
        ]}
      />
    </>
  );
};
