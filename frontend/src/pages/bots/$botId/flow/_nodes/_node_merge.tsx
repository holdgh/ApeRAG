import { ApeNode, ApeNodeVar } from '@/types';
import { CaretRightOutlined } from '@ant-design/icons';
import { applyNodeChanges, NodeChange } from '@xyflow/react';
import { Collapse, Form, Select, Switch, theme, Typography } from 'antd';
import _ from 'lodash';
import { useEffect, useMemo } from 'react';
import { FormattedMessage, useIntl, useModel } from 'umi';
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

  const sourceNodes = useMemo(() => {
    const nid = originNode?.id;
    const connects = edges.filter((edg) => edg.target === nid);
    return connects.map((edg) => nodes.find((nod) => nod.id === edg.source));
  }, [edges, nodes]);

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

  useEffect(() => {
    const vars = originNode?.data.vars;
    sourceNodes.forEach((nd) => {
      const item = vars?.find((v) => v.ref_node === nd?.id);
      const value: ApeNodeVar = {
        name: `${nd?.type}_docs`,
        source_type: 'dynamic',
        ref_node: nd?.id,
        ref_field: `${nd?.type}_docs`,
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
          label: formatMessage({ id: 'flow.merge.params' }),
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
                style={{ marginBottom: 0 }}
                label={formatMessage({ id: 'flow.merge.deduplicate' })}
                valuePropName="checked"
                tooltip={formatMessage({ id: 'flow.merge.deduplicate.tips' })}
              >
                <Switch size="small" />
              </Form.Item>
            </Form>
          ),
        },
        {
          key: '2',
          label: formatMessage({ id: 'flow.merge.step' }),
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
              <FormattedMessage id="flow.merge.empty" />
            </Typography.Text>
          ),
        },
      ]}
    />
  );
};
