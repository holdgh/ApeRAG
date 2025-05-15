import { ModelSelect } from '@/components';
import { ApeNode, ApeNodeVar } from '@/types';
import { CaretRightOutlined } from '@ant-design/icons';
import { applyNodeChanges, NodeChange } from '@xyflow/react';
import { Collapse, Form, Input, Space, theme } from 'antd';
import _ from 'lodash';
import { useEffect, useMemo } from 'react';
import { useIntl, useModel } from 'umi';
import { getCollapsePanelStyle } from './_styles';

type VarType = {
  model: string;
};
export const ApeNodeRerank = ({ node }: { node: ApeNode }) => {
  const { token } = theme.useToken();
  const { formatMessage } = useIntl();
  const { nodes, edges, setNodes } = useModel('bots.$botId.flow.model');
  const originNode = useMemo(() => nodes.find((n) => n.id === node.id), [node]);
  const [form] = Form.useForm<VarType>();

  const refDocNode = useMemo(() => {
    const nid = originNode?.id;
    const connects = edges.filter((edg) => edg.target === nid);
    const sourceNodes = connects.map((edg) =>
      nodes.find((nod) => nod.id === edg.source),
    );
    return _.size(sourceNodes) === 1 ? _.first(sourceNodes) : undefined;
  }, [edges, nodes]);

  const onValuesChange = (changedValues: VarType) => {
    if (!originNode) return;

    const vars = originNode?.data.vars;
    const varModel = vars?.find((item) => item.name === 'model');

    if (varModel && changedValues.model !== undefined) {
      varModel.value = changedValues.model;
    }
  };

  useEffect(() => {
    const model = String(
      originNode?.data.vars?.find((item) => item.name === 'model')?.value,
    );
    form.setFieldsValue({ model });
  }, [originNode]);

  useEffect(() => {
    if (!originNode?.id) return;
    const vars = originNode?.data.vars;
    const item = vars?.find((item) => item.name === 'docs');
    const value: ApeNodeVar = {
      name: `docs`,
      source_type: 'dynamic',
      ref_node: refDocNode?.id || '',
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
          id: originNode?.id,
          type: 'replace',
          item: {
            ...originNode,
          },
        },
      ];
      return applyNodeChanges(changes, nds);
    });
  }, [refDocNode]);

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
                name="model"
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
                tooltip={formatMessage({ id: 'flow.connection.required' })}
              >
                <Input
                  variant="filled"
                  disabled
                  style={{ borderWidth: 0, color: token.colorText }}
                  value={
                    refDocNode
                      ? refDocNode?.ariaLabel ||
                        formatMessage({
                          id: `flow.node.type.${refDocNode?.type}`,
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
