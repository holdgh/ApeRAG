import { ModelSelect } from '@/components';
import { ApeNode, ApeNodeType } from '@/types';
import { CaretRightOutlined } from '@ant-design/icons';
import { applyNodeChanges, NodeChange } from '@xyflow/react';
import { Collapse, Form, Input, InputNumber, Slider, theme } from 'antd';
import _ from 'lodash';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { useIntl, useModel } from 'umi';
import { ConnectInfoInput } from './_connect-info-input';
import { GlobalVars } from './_global-var';
import { getCollapsePanelStyle } from './_styles';

export const ApeNodeLlm = ({ node }: { node: ApeNode }) => {
  const { token } = theme.useToken();
  const { nodes, setNodes, edges, getNodeConfig } = useModel(
    'bots.$botId.flow.model',
  );
  const { getProviderByModelName } = useModel('models');
  const { formatMessage } = useIntl();

  const applyChanges = () => {
    setNodes((nds) => {
      const changes: NodeChange[] = [
        { id: node.id, type: 'replace', item: node },
      ];
      return applyNodeChanges(changes, nds);
    });
  };

  const getVarByName = useCallback(
    (name: string) => {
      return node.data.vars?.find((item) => item.name === name);
    },
    [node],
  );

  const [
    varModelName,
    varModelServiceProvider,
    varPromptTemplate,
    varTemperature,
    varMaxTokens,
    varQuery,
    varDocs,
  ] = useMemo(
    () => [
      getVarByName('model_name'),
      getVarByName('model_service_provider'),
      getVarByName('prompt_template'),
      getVarByName('temperature'),
      getVarByName('max_tokens'),
      getVarByName('query'),
      getVarByName('docs'),
    ],
    [getVarByName],
  );

  const [promptTemplate, setPromptemplate] = useState<string>(
    varPromptTemplate?.value,
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
    if (varPromptTemplate) {
      varPromptTemplate.value = promptTemplate;
    }
  }, [promptTemplate]);

  useEffect(() => {
    const vars = node.data.vars || [];
    if (!varModelName) {
      vars?.push({ name: 'model_name', value: '' });
    }
    if (!varModelServiceProvider) {
      vars?.push({ name: 'model_service_provider', value: '' });
    }
    if (!varPromptTemplate) {
      vars?.push({ name: 'prompt_template', value: '' });
      setPromptemplate(
        formatMessage(
          { id: 'model.prompt_template.default' },
          { query: '{query}', context: '{context}' },
        ),
      );
    }
    if (!varTemperature) {
      vars?.push({ name: 'temperature', value: 0.7 });
    }
    if (!varMaxTokens) {
      vars?.push({ name: 'max_tokens', value: 1000 });
    }
    if (!varQuery) {
      vars?.push({ name: 'query', source_type: 'global', global_var: 'query' });
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
            label: formatMessage({ id: 'flow.llm.params' }),
            style: getCollapsePanelStyle(token),
            children: (
              <>
                <Form layout="vertical" autoComplete="off">
                  <Form.Item
                    required
                    label={formatMessage({ id: 'model.name' })}
                    tooltip={formatMessage({ id: 'model.llm.tips' })}
                  >
                    <ModelSelect
                      model="completion"
                      variant="filled"
                      value={varModelName?.value}
                      onChange={(name) => {
                        if (varModelName) {
                          varModelName.value = name;
                        }
                        if (varModelServiceProvider) {
                          varModelServiceProvider.value =
                            getProviderByModelName(
                              name,
                              'completion',
                            ).provider?.name;
                        }
                        applyChanges();
                      }}
                    />
                  </Form.Item>
                  <Form.Item
                    required
                    label={formatMessage({ id: 'flow.temperature' })}
                    tooltip={formatMessage({ id: 'flow.temperature.tips' })}
                  >
                    <Slider
                      style={{ margin: 0 }}
                      min={0}
                      max={1}
                      step={0.01}
                      value={varTemperature?.value}
                      onChange={(value) => {
                        if (varTemperature) {
                          varTemperature.value = value;
                        }
                        applyChanges();
                      }}
                    />
                  </Form.Item>
                  <Form.Item
                    required
                    label={formatMessage({ id: 'flow.max_tokens' })}
                  >
                    <InputNumber
                      min={100}
                      max={2000}
                      step={10}
                      variant="filled"
                      style={{ width: '100%' }}
                      value={varMaxTokens?.value}
                      onChange={(value) => {
                        if (varMaxTokens) {
                          varMaxTokens.value = value;
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
              </>
            ),
          },
          {
            key: '2',
            label: formatMessage({ id: 'model.prompt_template' }),
            style: getCollapsePanelStyle(token),
            children: (
              <Input.TextArea
                variant="filled"
                value={promptTemplate}
                style={{ fontSize: 12 }}
                autoSize
                onChange={(e) => {
                  setPromptemplate(e.currentTarget.value);
                }}
              />
            ),
          },
          {
            key: '3',
            label: formatMessage({ id: 'flow.input.params' }),
            style: getCollapsePanelStyle(token),
            children: <GlobalVars />,
          },
        ]}
      />
    </>
  );
};
