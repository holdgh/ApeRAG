import { ApeNode } from '@/types';
import { CaretRightOutlined } from '@ant-design/icons';
import { applyNodeChanges, NodeChange } from '@xyflow/react';
import { Collapse, Form, Select, Switch, theme } from 'antd';
import _ from 'lodash';
import { useCallback, useEffect, useMemo } from 'react';
import { useIntl, useModel } from 'umi';
import { NodeInput } from './_node-input';
import { getCollapsePanelStyle } from './_styles';

export const ApeNodeMerge = ({ node }: { node: ApeNode }) => {
  const { token } = theme.useToken();
  const { formatMessage } = useIntl();
  const { nodes, setNodes, edges } = useModel('bots.$botId.flow.model');

  const values = useMemo(
    () => node.data.input.values || [],
    [node.data.input.values],
  );

  const applyChanges = useCallback(() => {
    setNodes((nds) => {
      const changes: NodeChange[] = [
        { id: node.id, type: 'replace', item: node },
      ];
      return applyNodeChanges(changes, nds);
    });
  }, [node]);

  const { refVectorSearchNode, refKeywordSearchNode } = useMemo(() => {
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
    };
  }, [edges, nodes]);

  useEffect(() => {
    _.set(
      values,
      'vector_search_docs',
      refVectorSearchNode?.id
        ? `{{ nodes.${refVectorSearchNode.id}.output.docs }}`
        : '',
    );
    applyChanges();
  }, [refVectorSearchNode]);

  useEffect(() => {
    _.set(
      values,
      'keyword_search_docs',
      refKeywordSearchNode?.id
        ? `{{ nodes.${refKeywordSearchNode.id}.output.docs }}`
        : '',
    );
    applyChanges();
  }, [refKeywordSearchNode]);

  return (
    <>
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
                    value={_.get(values, 'merge_strategy')}
                    onChange={(name) => {
                      _.set(values, 'merge_strategy', name);
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
                    checked={_.get(values, 'deduplicate')}
                    onChange={(checked) => {
                      _.set(values, 'deduplicate', checked);
                      applyChanges();
                    }}
                  />
                </Form.Item>
                <Form.Item
                  required
                  label={formatMessage({ id: 'flow.vector_search.source' })}
                >
                  <NodeInput
                    disabled
                    variant="filled"
                    placeholder={formatMessage({
                      id: 'flow.connection.required',
                    })}
                    value={_.get(values, 'vector_search_docs')}
                    onChange={(e) => {
                      _.set(
                        values,
                        'vector_search_docs',
                        e.currentTarget.value,
                      );
                      applyChanges();
                    }}
                  />
                </Form.Item>
                <Form.Item
                  required
                  style={{ marginBottom: 0 }}
                  label={formatMessage({ id: 'flow.keyword_search.source' })}
                >
                  <NodeInput
                    disabled
                    variant="filled"
                    placeholder={formatMessage({
                      id: 'flow.connection.required',
                    })}
                    value={_.get(values, 'keyword_search_docs')}
                    onChange={(e) => {
                      _.set(
                        values,
                        'keyword_search_docs',
                        e.currentTarget.value,
                      );
                      applyChanges();
                    }}
                  />
                </Form.Item>
              </Form>
            ),
          },
          {
            key: '2',
            label: formatMessage({ id: 'flow.output.params' }),
            style: getCollapsePanelStyle(token),
            children: <></>,
          },
        ]}
      />
    </>
  );
};
