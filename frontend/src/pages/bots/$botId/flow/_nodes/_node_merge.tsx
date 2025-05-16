import { ApeNode, ApeNodeType, ApeNodeVar } from '@/types';
import { CaretRightOutlined } from '@ant-design/icons';
import { applyNodeChanges, NodeChange } from '@xyflow/react';
import { Collapse, Form, Select, Switch, theme } from 'antd';
import { useCallback, useEffect, useMemo } from 'react';
import { useIntl, useModel } from 'umi';
import { ConnectInfoInput } from './_connect-info-input';
import { getCollapsePanelStyle } from './_styles';

type VarType = {
  merge_strategy: 'union';
  deduplicate: boolean;
};

export const ApeNodeMerge = ({ node }: { node: ApeNode }) => {
  const { token } = theme.useToken();
  const { formatMessage } = useIntl();
  const { nodes, setNodes, edges, getNodeConfig } = useModel(
    'bots.$botId.flow.model',
  );
  const [form] = Form.useForm<VarType>();

  const {
    refVectorSearchNode,
    refKeywordSearchNode,
    vectorSearchNodeConfig,
    keywordSearchNodeConfig,
  } = useMemo(() => {
    const nid = node?.id;
    const connects = edges.filter((edg) => edg.target === nid);
    const sourceNodes = connects.map((edg) =>
      nodes.find((nod) => nod.id === edg.source),
    );
    const _refVectorSearchNode = sourceNodes?.find(
      (nod) => nod?.type === 'vector_search',
    );
    const _refKeywordSearchNode = sourceNodes?.find(
      (nod) => nod?.type === 'keyword_search',
    );
    return {
      refVectorSearchNode: _refVectorSearchNode,
      refKeywordSearchNode: _refKeywordSearchNode,
      vectorSearchNodeConfig: getNodeConfig(
        _refVectorSearchNode?.type as ApeNodeType,
        _refVectorSearchNode?.ariaLabel ||
          formatMessage({ id: `flow.node.type.vector_search` }),
      ),
      keywordSearchNodeConfig: getNodeConfig(
        _refKeywordSearchNode?.type as ApeNodeType,
        _refKeywordSearchNode?.ariaLabel ||
          formatMessage({ id: `flow.node.type.keyword_search` }),
      ),
    };
  }, [edges, nodes]);

  /**
   * on node form change
   */
  const onValuesChange = useCallback(
    (changedValues: VarType) => {
      if (!node) return;
      const vars = node?.data.vars;
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
            id: node.id,
            type: 'replace',
            item: {
              ...node,
            },
          },
        ];
        return applyNodeChanges(changes, nds);
      });
    },
    [node],
  );

  /**
   * init node form data
   */
  useEffect(() => {
    const merge_strategy = (node?.data.vars?.find(
      (item) => item.name === 'merge_strategy',
    )?.value || 'union') as VarType['merge_strategy'];
    const deduplicate = Boolean(
      node?.data.vars?.find((item) => item.name === 'deduplicate')?.value,
    );
    form.setFieldsValue({ merge_strategy, deduplicate });
  }, []);

  /**
   * node ref change
   */
  useEffect(() => {
    const vars = node?.data.vars;
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
          id: node.id,
          type: 'replace',
          item: {
            ...node,
          },
        },
      ];
      return applyNodeChanges(changes, nds);
    });
  }, [refVectorSearchNode?.id, refKeywordSearchNode?.id]);

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
                  suffixIcon={null}
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
              >
                <ConnectInfoInput
                  refNode={refVectorSearchNode}
                  refNodeConfig={vectorSearchNodeConfig}
                />
              </Form.Item>
              <Form.Item
                required
                style={{ marginBottom: 0 }}
                label={formatMessage({ id: 'flow.keyword_search.source' })}
              >
                <ConnectInfoInput
                  refNode={refKeywordSearchNode}
                  refNodeConfig={keywordSearchNodeConfig}
                />
              </Form.Item>
            </Form>
          ),
        },
      ]}
    />
  );
};
