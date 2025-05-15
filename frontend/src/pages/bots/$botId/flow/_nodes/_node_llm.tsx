import { ModelSelect } from '@/components';
import { ApeNode, ApeNodeVar } from '@/types';
import {
  CaretRightOutlined,
  DeleteOutlined,
  PlusOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import {
  Button,
  Collapse,
  Form,
  InputNumber,
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
  model: string;
  temperature: number;
  max_tokens: number;
};

export const ApeNodeLlm = ({ node }: { node: ApeNode }) => {
  const { token } = theme.useToken();
  const { nodes } = useModel('bots.$botId.flow.model');
  const { formatMessage } = useIntl();

  const originNode = useMemo(() => nodes.find((n) => n.id === node.id), [node]);

  const [form] = Form.useForm<VarType>();

  const columns: TableProps<ApeNodeVar>['columns'] = [
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
    (item) => !_.includes(['model', 'temperature', 'max_tokens'], item.name),
  );

  const onValuesChange = (changedValues: VarType) => {
    if (!originNode) return;

    const vars = originNode?.data.vars;
    const varModel = vars?.find((item) => item.name === 'model');
    const varTemperature = vars?.find((item) => item.name === 'temperature');
    const varMaxTokens = vars?.find((item) => item.name === 'max_tokens');

    if (varModel && changedValues.model !== undefined) {
      varModel.value = changedValues.model;
    }

    if (varTemperature && changedValues.temperature !== undefined) {
      varTemperature.value = changedValues.temperature;
    }

    if (varMaxTokens && changedValues.max_tokens !== undefined) {
      varMaxTokens.value = changedValues.max_tokens;
    }
  };

  const onAddParams: React.MouseEventHandler<HTMLElement> = (e) => {
    e.stopPropagation();
  };

  useEffect(() => {
    const vars = originNode?.data.vars;
    const model = String(
      originNode?.data.vars?.find((item) => item.name === 'model')?.value,
    );
    const temperature = Number(
      vars?.find((item) => item.name === 'temperature')?.value || 0.7,
    );
    const max_tokens = Number(
      vars?.find((item) => item.name === 'max_tokens')?.value || 1000,
    );
    form.setFieldsValue({ model, temperature, max_tokens });
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
                    name="model"
                    tooltip={formatMessage({ id: 'model.llm.tips' })}
                  >
                    <ModelSelect model="completion" variant="filled" />
                  </Form.Item>
                  <Form.Item
                    required
                    style={{ marginBottom: 0 }}
                    label={formatMessage({ id: 'flow.temperature' })}
                    name="temperature"
                    tooltip={formatMessage({ id: 'flow.temperature.tips' })}
                  >
                    <Slider style={{ margin: 0 }} min={0} max={1} step={0.01} />
                  </Form.Item>
                  <Form.Item
                    required
                    style={{ marginBottom: 0 }}
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
