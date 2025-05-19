import { ModelSelect } from '@/components';
import { ApeNode, ApeNodeType, ApeNodeVar } from '@/types';
import { CaretRightOutlined } from '@ant-design/icons';
import { applyNodeChanges, NodeChange } from '@xyflow/react';
import { Collapse, Form, Space, theme } from 'antd';
import _ from 'lodash';
import { useCallback, useEffect, useMemo } from 'react';
import { useIntl, useModel } from 'umi';
import { ConnectInfoInput } from './_connect-info-input';
import { getCollapsePanelStyle } from './_styles';

type VarType = {
  model_name: string;
};
export const ApeNodeRerank = ({ node }: { node: ApeNode }) => {
  const { token } = theme.useToken();
  const { formatMessage } = useIntl();
  const { nodes, edges, setNodes, getNodeConfig } = useModel(
    'bots.$botId.flow.model',
  );
  const { getProviderByModelName } = useModel('models');

  const [form] = Form.useForm<VarType>();

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

  /**
   * on node form change
   */
  const onValuesChange = useCallback(
    (changedValues: VarType) => {
      const vars = node?.data.vars;
      const varModelName = vars?.find((item) => item.name === 'model_name');
      const varModelServiceProvider = vars?.find(
        (item) => item.name === 'model_service_provider',
      );
      if (varModelName && changedValues.model_name !== undefined) {
        varModelName.value = changedValues.model_name;
        if (varModelServiceProvider) {
          const { provider } = getProviderByModelName(
            changedValues.model_name,
            'rerank',
          );
          varModelServiceProvider.value = provider?.name;
        }
      }
    },
    [node],
  );

  /**
   * init node form data
   */
  useEffect(() => {
    const model_name = String(
      node.data.vars?.find((item) => item.name === 'model_name')?.value,
    );
    form.setFieldsValue({ model_name });
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
          label: <Space>{formatMessage({ id: 'flow.input.params' })}</Space>,
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
                tooltip={formatMessage({ id: 'model.rerank.tips' })}
                label={formatMessage({ id: 'flow.reranker.model' })}
                name="model_name"
              >
                <ModelSelect
                  style={{ width: '100%' }}
                  model="rerank"
                  variant="filled"
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
  );
};
