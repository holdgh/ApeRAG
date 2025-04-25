import { ModelServiceProvider, SupportedModelServiceProvider } from '@/api';
import { PageContainer, PageHeader } from '@/components';
import { MODEL_PROVIDER_ICON } from '@/constants';
import { api } from '@/services';
import { EditOutlined } from '@ant-design/icons';
import {
  Avatar,
  Button,
  Divider,
  Form,
  Input,
  Modal,
  Space,
  Switch,
  Table,
  TableProps,
  Tooltip,
  Typography,
} from 'antd';
import { useEffect, useMemo, useState } from 'react';
import { BsRobot } from 'react-icons/bs';

import { useIntl, useModel } from 'umi';

type ListModelProvider = ModelServiceProvider & {
  enabled: boolean;
};

export default () => {
  const { loading, setLoading } = useModel('global');
  const { formatMessage } = useIntl();

  const [supportedModelProviders, setSupportedModelProviders] =
    useState<SupportedModelServiceProvider[]>();

  const [modelProviders, setModelProviders] =
    useState<ModelServiceProvider[]>();

  const [form] = Form.useForm<ListModelProvider>();

  const [visible, setVisible] = useState<boolean>(false);

  const [modal, contextHolder] = Modal.useModal();

  const providerName = Form.useWatch(['name'], form);
  const currentProvider = useMemo(
    () => supportedModelProviders?.find((s) => s.name === providerName),
    [providerName],
  );

  const getSupportedModelProviders = async () => {
    setLoading(true);
    const res = await api.supportedModelServiceProvidersGet();
    setSupportedModelProviders(res.data.items);
    setLoading(false);
  };
  const getModelProviders = async () => {
    setLoading(true);
    const res = await api.modelServiceProvidersGet();
    setModelProviders(res.data.items);
    setLoading(false);
  };

  const onEditProvider = async (item: ListModelProvider) => {
    setVisible(true);
    form.setFieldsValue(item);
  };

  const onUpdateProvider = async () => {
    setLoading(true);
    const provider = await form.validateFields();
    if (!provider.name) return;
    await api.modelServiceProvidersProviderPut({
      provider: provider.name,
      modelServiceProviderUpdate: provider,
    });
    await getModelProviders();
    setVisible(false);
    setLoading(false);
  };

  const onToggleProvider = async (enable: boolean, item: ListModelProvider) => {
    if (!item.name) return;

    if (enable) {
      // add model service provider
      await onEditProvider(item);
    } else {
      // delete model service provider
      const confirmed = await modal.confirm({
        title: formatMessage({ id: 'action.confirm' }),
        content: formatMessage(
          { id: 'model.provider.disable.confirm' },
          { label: item.label },
        ),
        okButtonProps: {
          danger: true,
        },
      });
      if (confirmed) {
        setLoading(true);
        await api.modelServiceProvidersProviderDelete({ provider: item.name });
        await getModelProviders();
        setLoading(false);
      }
    }
  };

  const columns: TableProps<ListModelProvider>['columns'] = [
    {
      title: formatMessage({ id: 'model.provider' }),
      dataIndex: 'label',
      render: (value, record) => {
        return (
          <Space>
            <Avatar
              shape="square"
              src={MODEL_PROVIDER_ICON[record.name || '']}
              icon={<BsRobot />}
            />
            <Typography.Text type={record.enabled ? undefined : 'secondary'}>
              {value}
            </Typography.Text>
          </Space>
        );
      },
    },
    {
      title: formatMessage({ id: 'model.provider.uri' }),
      dataIndex: 'base_url',
      render: (value, record) => (
        <Typography.Text type={record.enabled ? undefined : 'secondary'}>
          {value}
        </Typography.Text>
      ),
    },
    {
      title: formatMessage({ id: 'model.provider.api_key' }),
      dataIndex: 'api_key',
      render: (value, record) => (
        <Typography.Text type={record.enabled ? undefined : 'secondary'}>
          {value ? '************' : ''}
        </Typography.Text>
      ),
    },
    {
      title: formatMessage({ id: 'action.name' }),
      render: (value, record) => {
        return (
          <Space split={<Divider type="vertical" />}>
            <Tooltip
              title={formatMessage({
                id: record.enabled
                  ? 'model.provider.disable'
                  : 'model.provider.enable',
              })}
            >
              <Switch
                size="small"
                checked={record.enabled}
                onChange={(v) => onToggleProvider(v, record)}
              />
            </Tooltip>
            <Button
              disabled={!record.enabled}
              type="text"
              icon={<EditOutlined />}
              onClick={() => onEditProvider(record)}
            />
          </Space>
        );
      },
    },
  ];

  const listModelProviders: ListModelProvider[] = useMemo(
    () =>
      supportedModelProviders?.map((smp) => {
        const enabledProvider = modelProviders?.find(
          (mp) => mp.name === smp.name,
        );
        return {
          name: smp.name,
          enabled: enabledProvider !== undefined,
          label: enabledProvider?.label || smp.label,
          api_key: enabledProvider?.api_key,
          base_url: enabledProvider?.base_url || smp.base_url,
          allow_custom_base_url:
            enabledProvider?.allow_custom_base_url || smp.allow_custom_base_url,
        };
      }) || [],
    [supportedModelProviders, modelProviders],
  );

  useEffect(() => {
    form.setFieldValue('base_url', currentProvider?.base_url);
  }, [currentProvider]);

  useEffect(() => {
    getSupportedModelProviders();
    getModelProviders();
  }, []);

  return (
    <PageContainer>
      {contextHolder}
      <PageHeader
        title={formatMessage({ id: 'model.provider' })}
        description={formatMessage({ id: 'model.provider.description' })}
      ></PageHeader>
      <Table
        dataSource={listModelProviders}
        bordered
        rowKey="name"
        columns={columns}
        loading={loading}
        pagination={false}
      />
      <Modal
        title={formatMessage({ id: 'model.provider.settings' })}
        onCancel={() => setVisible(false)}
        onOk={onUpdateProvider}
        open={visible}
        width={580}
        okButtonProps={{
          loading,
        }}
      >
        <Divider />
        <Form layout="vertical" form={form}>
          <Form.Item
            name="name"
            hidden
            label={formatMessage({ id: 'model.provider' })}
            rules={[
              {
                required: true,
                message: formatMessage({ id: 'model.provider.required' }),
              },
            ]}
          >
            <Input />
          </Form.Item>
          {currentProvider?.allow_custom_base_url ? (
            <Form.Item
              name="base_url"
              label={formatMessage({ id: 'model.provider.uri' })}
              required
              rules={[
                {
                  required: true,
                  message: formatMessage({ id: 'model.provider.uri.required' }),
                },
              ]}
            >
              <Input
                placeholder={formatMessage({ id: 'model.provider.uri' })}
              />
            </Form.Item>
          ) : (
            <Form.Item
              label={formatMessage({ id: 'model.provider.uri' })}
              required
            >
              <Input disabled value={currentProvider?.base_url} />
            </Form.Item>
          )}

          <Form.Item
            name="api_key"
            label={formatMessage({ id: 'model.provider.api_key' })}
            rules={[
              {
                required: true,
                message: formatMessage({
                  id: 'model.provider.api_key.required',
                }),
              },
            ]}
          >
            <Input
              placeholder={formatMessage({ id: 'model.provider.api_key' })}
            />
          </Form.Item>
        </Form>
      </Modal>
    </PageContainer>
  );
};
