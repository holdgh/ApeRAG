import { ApeNode } from '@/types';
import { CaretRightOutlined } from '@ant-design/icons';
import { applyNodeChanges, NodeChange } from '@xyflow/react';
import { Collapse, Form, Select, Slider, theme } from 'antd';
import { useCallback, useEffect, useMemo } from 'react';
import { useIntl, useModel } from 'umi';
import { GlobalVars } from './_global-var';
import { getCollapsePanelStyle } from './_styles';

export const ApeNodeVectorSearch = ({ node }: { node: ApeNode }) => {
  const { token } = theme.useToken();
  const { setNodes } = useModel('bots.$botId.flow.model');
  const { formatMessage } = useIntl();
  const { collections } = useModel('collection');

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

  const [varTopK, varSimilarityThreshold, varCollectionIds, varQuery] = useMemo(
    () => [
      getVarByName('top_k'),
      getVarByName('similarity_threshold'),
      getVarByName('collection_ids'),
      getVarByName('query'),
    ],
    [getVarByName],
  );

  useEffect(() => {
    const vars = node.data.vars || [];
    if (!varTopK) {
      vars?.push({ name: 'top_k', value: 5 });
    }
    if (!varSimilarityThreshold) {
      vars?.push({ name: 'similarity_threshold', value: 0.2 });
    }
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
                  <Form.Item
                    required
                    label={formatMessage({ id: 'flow.top_k' })}
                    tooltip={formatMessage({ id: 'flow.top_k.tips' })}
                  >
                    <Slider
                      value={varTopK?.value}
                      style={{ margin: 0 }}
                      min={1}
                      max={10}
                      step={1}
                      onChange={(value) => {
                        if (varTopK) {
                          varTopK.value = value;
                        }
                        applyChanges();
                      }}
                    />
                  </Form.Item>
                  <Form.Item
                    required
                    style={{ marginBottom: 0 }}
                    label={formatMessage({ id: 'flow.similarity_threshold' })}
                    tooltip={formatMessage({
                      id: 'flow.similarity_threshold.tips',
                    })}
                  >
                    <Slider
                      value={varSimilarityThreshold?.value}
                      style={{ margin: 0 }}
                      min={0}
                      max={1}
                      step={0.01}
                      onChange={(value) => {
                        if (varSimilarityThreshold) {
                          varSimilarityThreshold.value = value;
                        }
                        applyChanges();
                      }}
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
            children: <GlobalVars />,
          },
        ]}
      />
    </>
  );
};
