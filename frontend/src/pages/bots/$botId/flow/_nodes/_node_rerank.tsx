import { ModelSelect } from '@/components';
import { ApeNode, ApeNodeVar } from '@/types';
import { CaretRightOutlined, QuestionCircleOutlined } from '@ant-design/icons';
import { Collapse, Form, Space, theme, Tooltip, Typography } from 'antd';
import _ from 'lodash';
import { useEffect, useMemo } from 'react';
import { FormattedMessage, useIntl, useModel } from 'umi';
import { getCollapsePanelStyle } from './_styles';

type VarType = {
  model: string;
};
export const ApeNodeRerank = ({ node }: { node: ApeNode }) => {
  const { token } = theme.useToken();
  const { formatMessage } = useIntl();
  const { nodes, edges } = useModel('bots.$botId.flow.model');
  const originNode = useMemo(() => nodes.find((n) => n.id === node.id), [node]);
  const [form] = Form.useForm<VarType>();

  const sourceNodes = useMemo(() => {
    const nid = originNode?.id;
    const connects = edges.filter((edg) => edg.target === nid);
    return connects.map((edg) => nodes.find((nod) => nod.id === edg.source));
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
    const vars = originNode?.data.vars;
    sourceNodes.forEach((nd) => {
      const item = vars?.find((v) => v.ref_node === nd?.id);
      const value: ApeNodeVar = {
        name: `docs`,
        source_type: 'dynamic',
        ref_node: nd?.id,
        ref_field: `docs`,
      };
      if (item) {
        Object.assign(item, value);
      } else {
        vars?.push(value);
      }
    });
  }, [sourceNodes]);

  useEffect(() => {
    if (!originNode) return;
    originNode.data.vars = _.filter(originNode?.data.vars, (item) => {
      if (item.source_type !== 'dynamic') return true;
      return Boolean(
        edges.find(
          (edg) =>
            edg.source === item.ref_node && edg.target === originNode?.id,
        ),
      );
    });
  }, [edges, originNode]);

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
          label: (
            <Space>
              {formatMessage({ id: 'flow.reranker.model' })}
              <Tooltip title={formatMessage({ id: 'model.rerank.tips' })}>
                <Typography.Text type="secondary">
                  <QuestionCircleOutlined />
                </Typography.Text>
              </Tooltip>
            </Space>
          ),
          style: getCollapsePanelStyle(token),
          children: (
            <Form
              form={form}
              layout="vertical"
              onValuesChange={onValuesChange}
              autoComplete="off"
            >
              <Form.Item name="model" style={{ marginBottom: 0 }}>
                <ModelSelect
                  style={{ width: '100%' }}
                  model="rerank"
                  variant="filled"
                />
              </Form.Item>
            </Form>
          ),
        },
        {
          key: '2',
          label: formatMessage({ id: 'flow.reranker.target' }),
          style: getCollapsePanelStyle(token),
          children: _.size(sourceNodes) ? (
            <Typography>
              <ul>
                {sourceNodes.map((node) => {
                  return (
                    <li key={node?.id}>
                      {node?.ariaLabel ||
                        formatMessage({ id: `flow.node.type.${node?.type}` })}
                    </li>
                  );
                })}
              </ul>
            </Typography>
          ) : (
            <Typography.Text type="danger">
              <FormattedMessage id="flow.reranker.empty" />
            </Typography.Text>
          ),
        },
      ]}
    />
  );
};
