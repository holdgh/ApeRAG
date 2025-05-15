import { ApeNode, ApeNodeVar } from '@/types';
import { CaretRightOutlined } from '@ant-design/icons';
import { applyNodeChanges, NodeChange } from '@xyflow/react';
import { Collapse, Form, Input, Select, Switch, theme } from 'antd';
import { useEffect, useMemo } from 'react';
import { useIntl, useModel } from 'umi';
import { getCollapsePanelStyle } from './_styles';

type VarType = {
  merge_strategy: 'union';
  deduplicate: boolean;
};

export const ApeNodeMerge = ({ node }: { node: ApeNode }) => {
  const { token } = theme.useToken();
  const { formatMessage } = useIntl();
  const { nodes, setNodes, edges } = useModel('bots.$botId.flow.model');
  const originNode = useMemo(() => nodes.find((n) => n.id === node.id), [node]);
  const [form] = Form.useForm<VarType>();

  const { refVectorSearchNode, refKeywordSearchNode } = useMemo(() => {
    const nid = originNode?.id;
    const connects = edges.filter((edg) => edg.target === nid);
    const sourceNodes = connects.map((edg) =>
      nodes.find((nod) => nod.id === edg.source),
    );
    return {
      refVectorSearchNode: sourceNodes?.find(
        (nod) => nod?.type === 'vector_search',
      ),
      refKeywordSearchNode: sourceNodes?.find(
        (nod) => nod?.type === 'keyword_search',
      ),
    };
  }, [edges, nodes]);

  useEffect(() => {
    if (!originNode?.id) return;
    const vars = originNode?.data.vars;
    const vectorSearchDocsItem = vars?.find(
      (item) => item.name === 'vector_search_docs',
    );
    const keyworkSearchDocsItem = vars?.find(
      (item) => item.name === 'keyword_search_docs',
    );

    const vectorSearchDocsValue: ApeNodeVar = {
      name: `vector_search_docs`,
      source_type: 'dynamic',
      ref_node: refVectorSearchNode?.id || '',
      ref_field: `vector_search_docs`,
    };
    const keyworkSearchDocsValue: ApeNodeVar = {
      name: `keyword_search_docs`,
      source_type: 'dynamic',
      ref_node: refKeywordSearchNode?.id || '',
      ref_field: `keyword_search_docs`,
    };

    if (vectorSearchDocsItem) {
      Object.assign(vectorSearchDocsItem, vectorSearchDocsValue);
    } else {
      vars?.push(vectorSearchDocsValue);
    }

    if (keyworkSearchDocsItem) {
      Object.assign(keyworkSearchDocsItem, keyworkSearchDocsValue);
    } else {
      vars?.push(keyworkSearchDocsValue);
    }

    setNodes((nds) => {
      const changes: NodeChange[] = [
        {
          id: originNode?.id,
          type: 'replace',
          item: {
            ...originNode,
          },
        },
      ];
      return applyNodeChanges(changes, nds);
    });
  }, [refVectorSearchNode, refKeywordSearchNode]);

  const onValuesChange = (changedValues: VarType) => {
    if (!originNode) return;

    const vars = originNode?.data.vars;
    const varMergeAtrategy = vars?.find(
      (item) => item.name === 'merge_strategy',
    );
    const varDeduplicate = vars?.find((item) => item.name === 'deduplicate');

    if (varMergeAtrategy && changedValues.merge_strategy !== undefined) {
      varMergeAtrategy.value = changedValues.merge_strategy;
    }

    if (varDeduplicate && changedValues.deduplicate !== undefined) {
      varDeduplicate.value = changedValues.deduplicate;
    }

    setNodes((nds) => {
      const changes: NodeChange[] = [
        {
          id: originNode.id,
          type: 'replace',
          item: {
            ...originNode,
          },
        },
      ];
      return applyNodeChanges(changes, nds);
    });
  };

  useEffect(() => {
    const merge_strategy = (originNode?.data.vars?.find(
      (item) => item.name === 'merge_strategy',
    )?.value || 'union') as VarType['merge_strategy'];
    const deduplicate = Boolean(
      originNode?.data.vars?.find((item) => item.name === 'deduplicate')?.value,
    );
    form.setFieldsValue({ merge_strategy, deduplicate });
  }, [originNode]);

  return (
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
          label: formatMessage({ id: 'flow.input.params' }),
          style: getCollapsePanelStyle(token),
          children: (
            <Form
              form={form}
              layout="vertical"
              onValuesChange={onValuesChange}
              autoComplete="off"
            >
              <Form.Item
                required
                name="merge_strategy"
                label={formatMessage({ id: 'flow.merge.merge_strategy' })}
              >
                <Select
                  variant="filled"
                  options={[{ label: 'Union', value: 'union' }]}
                />
              </Form.Item>
              <Form.Item
                required
                name="deduplicate"
                label={formatMessage({ id: 'flow.merge.deduplicate' })}
                valuePropName="checked"
                tooltip={formatMessage({ id: 'flow.merge.deduplicate.tips' })}
              >
                <Switch size="small" />
              </Form.Item>
              <Form.Item
                required
                label={formatMessage({ id: 'flow.vector_search.source' })}
                tooltip={formatMessage({ id: 'flow.connection.required' })}
              >
                <Input
                  variant="filled"
                  disabled
                  style={{ borderWidth: 0, color: token.colorText }}
                  value={
                    refVectorSearchNode
                      ? refVectorSearchNode?.ariaLabel ||
                        formatMessage({
                          id: `flow.node.type.${refVectorSearchNode?.type}`,
                        })
                      : ''
                  }
                />
              </Form.Item>
              <Form.Item
                required
                style={{ marginBottom: 0 }}
                label={formatMessage({ id: 'flow.keyword_search.source' })}
                tooltip={formatMessage({ id: 'flow.connection.required' })}
              >
                <Input
                  variant="filled"
                  disabled
                  style={{ borderWidth: 0, color: token.colorText }}
                  value={
                    refKeywordSearchNode
                      ? refKeywordSearchNode?.ariaLabel ||
                        formatMessage({
                          id: `flow.node.type.${refKeywordSearchNode?.type}`,
                        })
                      : ''
                  }
                />
              </Form.Item>
            </Form>
          ),
        },
      ]}
    />
  );
};
