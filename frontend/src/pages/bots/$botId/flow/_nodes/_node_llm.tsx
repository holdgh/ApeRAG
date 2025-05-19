import { ModelSelect } from '@/components';
import { ApeNode, ApeNodeConfig, ApeNodeType, ApeNodeVar } from '@/types';
import { CaretRightOutlined } from '@ant-design/icons';
import { applyNodeChanges, NodeChange } from '@xyflow/react';
import { Collapse, Form, Input, InputNumber, Slider, Table, theme } from 'antd';
import _ from 'lodash';
import { useCallback, useEffect, useMemo } from 'react';
import { useIntl, useModel } from 'umi';
import { ConnectInfoInput } from './_connect-info-input';
import { getCollapsePanelStyle } from './_styles';

type VarType = {
  model_name: string;
  prompt_template?: string;
  temperature: number;
  max_tokens: number;
};

export const ApeNodeLlm = ({ node }: { node: ApeNode }) => {
  const { token } = theme.useToken();
  const [form] = Form.useForm<VarType>();
  const { nodes, setNodes, edges, getNodeGlobalVars, getNodeConfig } = useModel(
    'bots.$botId.flow.model',
  );
  const { getProviderByModelName } = useModel('models');
  const { formatMessage } = useIntl();

  const { refNode, refNodeConfig } = useMemo(() => {
    const nid = node?.id;
    const connects = edges.filter((edg) => edg.target === nid);
    const sourceNodes = connects.map((edg) =>
      nodes.find((nod) => nod.id === edg.source),
    );
    const _refNode =
      _.size(sourceNodes) === 1 ? _.first(sourceNodes) : undefined;
    const _refNodeConfig: ApeNodeConfig = _refNode
      ? getNodeConfig(
          _refNode.type as ApeNodeType,
          _refNode?.ariaLabel ||
            formatMessage({ id: `flow.node.type.${_refNode?.type}` }),
        )
      : {};
    return { refNode: _refNode, refNodeConfig: _refNodeConfig };
  }, [edges, nodes]);

  /**
   * on node form change
   */
  const onValuesChange = useCallback(
    (changedValues: VarType) => {
      if (!node) return;

      const vars = node?.data.vars;
      const varModelName = vars?.find((item) => item.name === 'model_name');
      const varModelServiceProvider = vars?.find(
        (item) => item.name === 'model_service_provider',
      );
      const varPromptTemplate = vars?.find(
        (item) => item.name === 'prompt_template',
      );
      const varTemperature = vars?.find((item) => item.name === 'temperature');
      const varMaxTokens = vars?.find((item) => item.name === 'max_tokens');

      if (varModelName && changedValues.model_name !== undefined) {
        varModelName.value = changedValues.model_name;
        if (varModelServiceProvider) {
          const { provider } = getProviderByModelName(
            changedValues.model_name,
            'completion',
          );
          varModelServiceProvider.value = provider?.name;
        }
      }
      if (varPromptTemplate && changedValues.prompt_template !== undefined) {
        varPromptTemplate.value = changedValues.prompt_template;
      }
      if (varTemperature && changedValues.temperature !== undefined) {
        varTemperature.value = changedValues.temperature;
      }
      if (varMaxTokens && changedValues.max_tokens !== undefined) {
        varMaxTokens.value = changedValues.max_tokens;
      }
    },
    [node],
  );

  /**
   * init node form data
   */
  useEffect(() => {
    const vars = node?.data.vars;
    const model_name = String(
      node?.data.vars?.find((item) => item.name === 'model_name')?.value,
    );
    const prompt_template = String(
      node?.data.vars?.find((item) => item.name === 'prompt_template')?.value,
    );

    const temperature = Number(
      vars?.find((item) => item.name === 'temperature')?.value || 0.7,
    );
    const max_tokens = Number(
      vars?.find((item) => item.name === 'max_tokens')?.value || 1000,
    );
    form.setFieldsValue({
      model_name,
      prompt_template,
      temperature,
      max_tokens,
    });
  }, []);

  /**
   * node ref change
   */
  useEffect(() => {
    const vars = node?.data.vars;
    const item = vars?.find((item) => item.name === 'docs');
    const value: ApeNodeVar = {
      name: `docs`,
      source_type: 'dynamic',
      ref_node: refNode?.id || '',
      ref_field: `docs`,
    };

    if (item) {
      Object.assign(item, value);
    } else {
      vars?.push(value);
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
  }, [refNode?.id]);

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
                <Form
                  form={form}
                  layout="vertical"
                  onValuesChange={onValuesChange}
                  autoComplete="off"
                >
                  <Form.Item
                    required
                    label={formatMessage({ id: 'model.name' })}
                    name="model_name"
                    tooltip={formatMessage({ id: 'model.llm.tips' })}
                  >
                    <ModelSelect model="completion" variant="filled" />
                  </Form.Item>
                  <Form.Item
                    required
                    label={formatMessage({ id: 'model.prompt_template' })}
                    name="prompt_template"
                  >
                    <Input.TextArea variant="filled" />
                  </Form.Item>
                  <Form.Item
                    required
                    label={formatMessage({ id: 'flow.temperature' })}
                    name="temperature"
                    tooltip={formatMessage({ id: 'flow.temperature.tips' })}
                  >
                    <Slider style={{ margin: 0 }} min={0} max={1} step={0.01} />
                  </Form.Item>
                  <Form.Item
                    required
                    label={formatMessage({ id: 'flow.max_tokens' })}
                    name="max_tokens"
                  >
                    <InputNumber
                      min={100}
                      max={2000}
                      step={10}
                      variant="filled"
                      style={{ width: '100%' }}
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
