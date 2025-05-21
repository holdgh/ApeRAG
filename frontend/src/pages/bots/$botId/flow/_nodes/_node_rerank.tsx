import { ModelSelect } from '@/components';
import { ApeNode, ApeNodeType } from '@/types';
import { CaretRightOutlined } from '@ant-design/icons';
import { applyNodeChanges, NodeChange } from '@xyflow/react';
import { Collapse, Form, Space, theme } from 'antd';
import _ from 'lodash';
import { useCallback, useEffect, useMemo } from 'react';
import { useIntl, useModel } from 'umi';
import { ConnectInfoInput } from './_connect-info-input';
import { getCollapsePanelStyle } from './_styles';

export const ApeNodeRerank = ({ node }: { node: ApeNode }) => {
  const { token } = theme.useToken();
  const { formatMessage } = useIntl();
  const { nodes, edges, setNodes, getNodeConfig } = useModel(
    'bots.$botId.flow.model',
  );
  const { getProviderByModelName } = useModel('models');

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

  const [varModelName, varModelServiceProvider, varDocs] = useMemo(
    () => [
      getVarByName('model_name'),
      getVarByName('model_service_provider'),
      getVarByName('docs'),
    ],
    [getVarByName],
  );

  const { refNode, refNodeConfig } = useMemo(() => {
    const nid = node.id;
    const connects = edges.filter((edg) => edg.target === nid);
    const sourceNodes = connects.map((edg) =>
      nodes.find((nod) => nod.id === edg.source),
    );
    const _refNode =
      _.size(sourceNodes) === 1 ? _.first(sourceNodes) : undefined;
    const _refNodeConfig = _refNode
      ? getNodeConfig(
          _refNode.type as ApeNodeType,
          _refNode?.ariaLabel ||
            formatMessage({ id: `flow.node.type.${_refNode?.type}` }),
        )
      : {};
    return { refNode: _refNode, refNodeConfig: _refNodeConfig };
  }, [edges, nodes]);

  useEffect(() => {
    if (refNode && varDocs) {
      varDocs.ref_node = refNode.id || '';
    }
  }, [refNode, varDocs]);

  useEffect(() => {
    const vars = node.data.vars || [];
    if (!varModelName) {
      vars?.push({ name: 'model_name', value: '' });
    }
    if (!varModelServiceProvider) {
      vars?.push({ name: 'model_service_provider', value: '' });
    }
    if (!varDocs) {
      vars?.push({
        name: 'docs',
        source_type: 'dynamic',
        ref_node: '',
        ref_field: 'docs',
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
        defaultActiveKey={['1']}
        style={{ background: 'none' }}
        items={[
          {
            key: '1',
            label: <Space>{formatMessage({ id: 'flow.input.params' })}</Space>,
            style: getCollapsePanelStyle(token),
            children: (
              <Form layout="vertical" autoComplete="off">
                <Form.Item
                  required
                  tooltip={formatMessage({ id: 'model.rerank.tips' })}
                  label={formatMessage({ id: 'flow.reranker.model' })}
                >
                  <ModelSelect
                    model="rerank"
                    variant="filled"
                    value={varModelName?.value}
                    onChange={(name) => {
                      if (varModelName) {
                        varModelName.value = name;
                      }
                      if (varModelServiceProvider) {
                        varModelServiceProvider.value = getProviderByModelName(
                          name,
                          'rerank',
                        ).provider?.name;
                      }
                      applyChanges();
                    }}
                  />
                </Form.Item>
                <Form.Item
                  required
                  style={{ marginBottom: 0 }}
                  label={formatMessage({ id: 'flow.input.source' })}
                >
                  <ConnectInfoInput
                    refNode={refNode}
                    refNodeConfig={refNodeConfig}
                  />
                </Form.Item>
              </Form>
            ),
          },
        ]}
      />
    </>
  );
};
