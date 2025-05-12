import { ApeNode, ApeNodeVars } from '@/types';
import {
  CaretRightOutlined,
  DeleteOutlined,
  PlusOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import { applyNodeChanges, NodeChange } from '@xyflow/react';
import {
  Button,
  Collapse,
  Form,
  Slider,
  Space,
  Table,
  TableProps,
  theme,
  Tooltip,
} from 'antd';
import _ from 'lodash';
import { useEffect, useMemo } from 'react';
import { FormattedMessage, useIntl, useModel } from 'umi';
import { getCollapsePanelStyle } from './_styles';

type VarType = {
  top_k: number;
  similarity_threshold: number;
};

export const ApeNodeVectorSearch = ({ node }: { node: ApeNode }) => {
  const { token } = theme.useToken();
  const { nodes, setNodes } = useModel('bots.$botId.flow.model');
  const { formatMessage } = useIntl();

  const originNode = useMemo(() => nodes.find((n) => n.id === node.id), [node]);

  const [form] = Form.useForm<VarType>();

  const columns: TableProps<ApeNodeVars>['columns'] = [
    {
      title: formatMessage({ id: 'flow.variable.title' }),
      dataIndex: 'name',
    },
    {
      title: formatMessage({ id: 'flow.variable.source_type' }),
      dataIndex: 'source_type',
    },
    {
      title: formatMessage({ id: 'flow.variable.value' }),
      dataIndex: 'global_var',
    },
    {
      title: formatMessage({ id: 'action.name' }),
      width: 60,
      render: () => {
        return (
          <Space>
            <Button type="text" size="small" icon={<SettingOutlined />} />
            <Button type="text" size="small" icon={<DeleteOutlined />} />
          </Space>
        );
      },
    },
  ];
  const records = originNode?.data.vars?.filter(
    (item) => !_.includes(['top_k', 'similarity_threshold'], item.name),
  );

  const onValuesChange = (changedValues: VarType) => {
    if (!originNode) return;

    const vars = originNode?.data.vars;
    const varTopK = vars?.find((item) => item.name === 'top_k');
    const varSimilarityThreshold = vars?.find(
      (item) => item.name === 'similarity_threshold',
    );

    if (varTopK && changedValues.top_k !== undefined) {
      varTopK.value = changedValues.top_k;
    }

    if (
      varSimilarityThreshold &&
      changedValues.similarity_threshold !== undefined
    ) {
      varSimilarityThreshold.value = changedValues.similarity_threshold;
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

  const onAddParams: React.MouseEventHandler<HTMLElement> = (e) => {
    e.stopPropagation();
  };

  useEffect(() => {
    const vars = originNode?.data.vars;
    const top_k = Number(vars?.find((item) => item.name === 'top_k')?.value);
    const similarity_threshold = Number(
      vars?.find((item) => item.name === 'similarity_threshold')?.value,
    );
    form.setFieldsValue({ top_k, similarity_threshold });
  }, [originNode]);

  return (
    <>
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
            label: formatMessage({ id: 'flow.vector.params' }),
            style: getCollapsePanelStyle(token),
            children: (
              <>
                <Form
                  size="small"
                  form={form}
                  layout="vertical"
                  onValuesChange={onValuesChange}
                  autoComplete="off"
                >
                  <Form.Item
                    required
                    style={{ marginBottom: 0 }}
                    label={formatMessage({ id: 'flow.top_k' })}
                    name="top_k"
                  >
                    <Slider style={{ margin: 0 }} min={1} max={10} step={1} />
                  </Form.Item>
                  <Form.Item
                    required
                    style={{ marginBottom: 0 }}
                    label={formatMessage({ id: 'flow.similarity_threshold' })}
                    name="similarity_threshold"
                  >
                    <Slider
                      style={{ margin: 0 }}
                      min={0.1}
                      max={1}
                      step={0.1}
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
            extra: (
              <Tooltip title={<FormattedMessage id="action.add" />}>
                <Button
                  type="link"
                  size="small"
                  icon={<PlusOutlined />}
                  onClick={onAddParams}
                />
              </Tooltip>
            ),
            children: (
              <Table
                rowKey="name"
                bordered
                size="small"
                pagination={false}
                columns={columns}
                dataSource={records}
                style={{ background: token.colorBgContainer }}
              />
            ),
          },
        ]}
      />
    </>
  );
};
