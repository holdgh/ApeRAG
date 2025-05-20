import { ApeNode, ApeNodeType } from '@/types';
import { CaretRightOutlined } from '@ant-design/icons';
import { applyNodeChanges, NodeChange } from '@xyflow/react';
import { Collapse, Form, Select, Switch, theme } from 'antd';
import { useCallback, useEffect, useMemo } from 'react';
import { useIntl, useModel } from 'umi';
import { ConnectInfoInput } from './_connect-info-input';
import { getCollapsePanelStyle } from './_styles';

export const ApeNodeMerge = ({ node }: { node: ApeNode }) => {
  const { token } = theme.useToken();
  const { formatMessage } = useIntl();
  const { nodes, setNodes, edges, getNodeConfig } = useModel(
    'bots.$botId.flow.model',
  );

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

  const [
    varMergeStrategy,
    varDeduplicate,
    varVectorSearchDocs,
    varKeywordSearchDocs,
  ] = useMemo(
    () => [
      getVarByName('merge_strategy'),
      getVarByName('deduplicate'),
      getVarByName('vector_search_docs'),
      getVarByName('keyword_search_docs'),
    ],
    [getVarByName],
  );

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

  useEffect(() => {
    if (refVectorSearchNode && varVectorSearchDocs) {
      varVectorSearchDocs.ref_node = refVectorSearchNode.id || '';
    }
  }, [refVectorSearchNode, varVectorSearchDocs]);

  useEffect(() => {
    if (refKeywordSearchNode && varKeywordSearchDocs) {
      varKeywordSearchDocs.ref_node = refKeywordSearchNode.id || '';
    }
  }, [refKeywordSearchNode, varKeywordSearchDocs]);

  useEffect(() => {
    const vars = node.data.vars || [];
    if (!varMergeStrategy) {
      vars?.push({ name: 'merge_strategy', value: 'union' });
    }
    if (!varDeduplicate) {
      vars?.push({ name: 'deduplicate', value: true });
    }
    if (!varVectorSearchDocs) {
      vars?.push({
        name: 'vector_search_docs',
        source_type: 'dynamic',
        ref_node: '',
        ref_field: 'vector_search_docs',
      });
    }
    if (!varKeywordSearchDocs) {
      vars?.push({
        name: 'keyword_search_docs',
        source_type: 'dynamic',
        ref_node: '',
        ref_field: 'keyword_search_docs',
      });
    }
    node.data.vars = vars;
    applyChanges();
  }, []);

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
            <Form layout="vertical" autoComplete="off">
              <Form.Item
                required
                label={formatMessage({ id: 'flow.merge.merge_strategy' })}
              >
                <Select
                  variant="filled"
                  suffixIcon={null}
                  options={[{ label: 'Union', value: 'union' }]}
                  value={varMergeStrategy?.value}
                  onChange={(name) => {
                    if (varMergeStrategy) {
                      varMergeStrategy.value = name;
                    }
                    applyChanges();
                  }}
                />
              </Form.Item>
              <Form.Item
                required
                label={formatMessage({ id: 'flow.merge.deduplicate' })}
                valuePropName="checked"
                tooltip={formatMessage({ id: 'flow.merge.deduplicate.tips' })}
              >
                <Switch
                  size="small"
                  checked={varDeduplicate?.value}
                  onChange={(checked) => {
                    if (varDeduplicate) {
                      varDeduplicate.value = checked;
                    }
                    applyChanges();
                  }}
                />
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
