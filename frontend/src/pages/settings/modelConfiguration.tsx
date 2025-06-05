import { PageContainer, PageHeader } from '@/components';
import { api } from '@/services';
import { LlmConfigurationResponse, LlmProvider, LlmProviderModel } from '@/api';
import { DeleteOutlined, EditOutlined, PlusOutlined } from '@ant-design/icons';
import {
  Button,
  Card,
  Col,
  Divider,
  Form,
  Input,
  InputNumber,
  Modal,
  Row,
  Select,
  Switch,
  Table,
  TableProps,
  Tag,
  Typography,
  message,
} from 'antd';
import { useCallback, useEffect, useState } from 'react';
import { useIntl, useModel } from 'umi';

export default () => {
  const { loading, setLoading } = useModel('global');
  const { formatMessage } = useIntl();

  const [configuration, setConfiguration] = useState<LlmConfigurationResponse>({
    providers: [],
    models: [],
  });

  // Provider form state
  const [providerForm] = Form.useForm();
  const [providerModalVisible, setProviderModalVisible] = useState(false);
  const [editingProvider, setEditingProvider] = useState<LlmProvider | null>(null);

  // Model form state
  const [modelForm] = Form.useForm();
  const [modelModalVisible, setModelModalVisible] = useState(false);
  const [editingModel, setEditingModel] = useState<LlmProviderModel | null>(null);

  const [modal, contextHolder] = Modal.useModal();

  // Fetch LLM configuration
  const fetchConfiguration = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.llmConfigurationGet();
      setConfiguration(res.data);
    } catch (error) {
      message.error('Failed to fetch LLM configuration');
    } finally {
      setLoading(false);
    }
  }, [setLoading]);

  // Provider operations
  const handleCreateProvider = useCallback(() => {
    setEditingProvider(null);
    providerForm.resetFields();
    // Set default values
    providerForm.setFieldsValue({
      completion_dialect: 'openai',
      embedding_dialect: 'openai',
      rerank_dialect: 'jina_ai',
      allow_custom_base_url: false,
    });
    setProviderModalVisible(true);
  }, [providerForm]);

  const handleEditProvider = useCallback((provider: LlmProvider) => {
    setEditingProvider(provider);
    providerForm.setFieldsValue(provider);
    setProviderModalVisible(true);
  }, [providerForm]);

  const handleSaveProvider = useCallback(async () => {
    try {
      const values = await providerForm.validateFields();
      setLoading(true);

      if (editingProvider) {
        // Update existing provider
        await api.llmProvidersProviderNamePut({
          providerName: editingProvider.name,
          llmProviderUpdate: values,
        });
        message.success('Provider updated successfully');
      } else {
        // Create new provider
        await api.llmProvidersPost({
          llmProviderCreate: values,
        });
        message.success('Provider created successfully');
      }

      setProviderModalVisible(false);
      await fetchConfiguration();
    } catch (error) {
      message.error('Failed to save provider');
    } finally {
      setLoading(false);
    }
  }, [editingProvider, providerForm, setLoading, fetchConfiguration]);

  const handleDeleteProvider = useCallback(async (provider: LlmProvider) => {
    const confirmed = await modal.confirm({
      title: formatMessage({ id: 'action.confirm' }),
      content: `确定要删除提供商 "${provider.label}" 吗？这将同时删除该提供商下的所有模型。`,
      okButtonProps: { danger: true },
    });

    if (confirmed) {
      setLoading(true);
      try {
        await api.llmProvidersProviderNameDelete({
          providerName: provider.name,
        });
        message.success('Provider deleted successfully');
        await fetchConfiguration();
      } catch (error) {
        message.error('Failed to delete provider');
      } finally {
        setLoading(false);
      }
    }
  }, [modal, formatMessage, setLoading, fetchConfiguration]);

  // Model operations
  const handleCreateModel = useCallback((providerName?: string) => {
    setEditingModel(null);
    modelForm.resetFields();
    if (providerName) {
      modelForm.setFieldValue('provider_name', providerName);
    }
    setModelModalVisible(true);
  }, [modelForm]);

  const handleEditModel = useCallback((model: LlmProviderModel) => {
    setEditingModel(model);
    modelForm.setFieldsValue(model);
    setModelModalVisible(true);
  }, [modelForm]);

  const handleSaveModel = useCallback(async () => {
    try {
      const values = await modelForm.validateFields();
      setLoading(true);

      if (editingModel) {
        // Update existing model
        await api.llmProvidersProviderNameModelsApiModelPut({
          providerName: editingModel.provider_name,
          api: editingModel.api as any,
          model: editingModel.model,
          llmProviderModelUpdate: values,
        });
        message.success('Model updated successfully');
      } else {
        // Create new model
        await api.llmProvidersProviderNameModelsPost({
          providerName: values.provider_name,
          llmProviderModelCreate: values,
        });
        message.success('Model created successfully');
      }

      setModelModalVisible(false);
      await fetchConfiguration();
    } catch (error) {
      message.error('Failed to save model');
    } finally {
      setLoading(false);
    }
  }, [editingModel, modelForm, setLoading, fetchConfiguration]);

  const handleDeleteModel = useCallback(async (model: LlmProviderModel) => {
    const confirmed = await modal.confirm({
      title: formatMessage({ id: 'action.confirm' }),
      content: `确定要删除模型 "${model.model}" 吗？`,
      okButtonProps: { danger: true },
    });

    if (confirmed) {
      setLoading(true);
      try {
        await api.llmProvidersProviderNameModelsApiModelDelete({
          providerName: model.provider_name,
          api: model.api as any,
          model: model.model,
        });
        message.success('Model deleted successfully');
        await fetchConfiguration();
      } catch (error) {
        message.error('Failed to delete model');
      } finally {
        setLoading(false);
      }
    }
  }, [modal, formatMessage, setLoading, fetchConfiguration]);

  // Handle API type change to auto-fill custom_llm_provider
  const handleApiTypeChange = useCallback((api: string) => {
    const currentProviderName = modelForm.getFieldValue('provider_name');
    if (currentProviderName) {
      const provider = configuration.providers.find(p => p.name === currentProviderName);
      if (provider) {
        let dialect = '';
        switch (api) {
          case 'completion':
            dialect = provider.completion_dialect;
            break;
          case 'embedding':
            dialect = provider.embedding_dialect;
            break;
          case 'rerank':
            dialect = provider.rerank_dialect;
            break;
        }
        modelForm.setFieldValue('custom_llm_provider', dialect);
      }
    }
  }, [modelForm, configuration.providers]);

  // Provider table columns
  const providerColumns: TableProps<LlmProvider>['columns'] = [
    {
      title: '提供商名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '显示名称',
      dataIndex: 'label',
      key: 'label',
    },
    {
      title: 'API基础URL',
      dataIndex: 'base_url',
      key: 'base_url',
      ellipsis: true,
    },
    {
      title: '允许自定义URL',
      dataIndex: 'allow_custom_base_url',
      key: 'allow_custom_base_url',
      render: (value: boolean) => <Switch checked={value} disabled />,
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record) => (
        <div>
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => handleEditProvider(record)}
          />
          <Button
            type="text"
            icon={<DeleteOutlined />}
            danger
            onClick={() => handleDeleteProvider(record)}
          />
          <Button
            type="text"
            size="small"
            onClick={() => handleCreateModel(record.name)}
          >
            添加模型
          </Button>
        </div>
      ),
    },
  ];

  // Model table columns
  const modelColumns: TableProps<LlmProviderModel>['columns'] = [
    {
      title: '提供商',
      dataIndex: 'provider_name',
      key: 'provider_name',
    },
    {
      title: 'API类型',
      dataIndex: 'api',
      key: 'api',
      render: (api: string) => (
        <Tag color={api === 'completion' ? 'blue' : api === 'embedding' ? 'green' : 'orange'}>
          {api}
        </Tag>
      ),
    },
    {
      title: '模型名称',
      dataIndex: 'model',
      key: 'model',
    },
    {
      title: '自定义提供商',
      dataIndex: 'custom_llm_provider',
      key: 'custom_llm_provider',
    },
    {
      title: '最大Token数',
      dataIndex: 'max_tokens',
      key: 'max_tokens',
      render: (value?: number) => value || '-',
    },
    {
      title: '标签',
      dataIndex: 'tags',
      key: 'tags',
      render: (tags: string[]) => (
        <>
          {tags.map(tag => (
            <Tag key={tag} size="small">{tag}</Tag>
          ))}
        </>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record) => (
        <div>
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => handleEditModel(record)}
          />
          <Button
            type="text"
            icon={<DeleteOutlined />}
            danger
            onClick={() => handleDeleteModel(record)}
          />
        </div>
      ),
    },
  ];

  useEffect(() => {
    fetchConfiguration();
  }, [fetchConfiguration]);

  return (
    <PageContainer>
      {contextHolder}
      <PageHeader
        title="模型配置"
        description="配置LLM提供商和模型"
      />

      {/* Providers Section */}
      <Card
        title="LLM提供商"
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleCreateProvider}
          >
            添加提供商
          </Button>
        }
        style={{ marginBottom: 24 }}
      >
        <Table
          columns={providerColumns}
          dataSource={configuration.providers}
          rowKey="name"
          loading={loading}
          pagination={false}
        />
      </Card>

      {/* Models Section */}
      <Card
        title="LLM模型"
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => handleCreateModel()}
          >
            添加模型
          </Button>
        }
      >
        <Table
          columns={modelColumns}
          dataSource={configuration.models}
          rowKey={(record) => `${record.provider_name}-${record.api}-${record.model}`}
          loading={loading}
          pagination={{ pageSize: 10 }}
        />
      </Card>

      {/* Provider Modal */}
      <Modal
        title={editingProvider ? '编辑提供商' : '添加提供商'}
        open={providerModalVisible}
        onCancel={() => setProviderModalVisible(false)}
        onOk={handleSaveProvider}
        width={600}
        confirmLoading={loading}
      >
        <Form form={providerForm} layout="vertical" style={{ marginTop: 16 }}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="name"
                label="提供商名称"
                rules={[{ required: true, message: '请输入提供商名称' }]}
              >
                <Input disabled={!!editingProvider} placeholder="例如: openai" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="label"
                label="显示名称"
                rules={[{ required: true, message: '请输入显示名称' }]}
              >
                <Input placeholder="例如: OpenAI" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="base_url"
            label="API基础URL"
            rules={[{ required: true, message: '请输入API基础URL' }]}
          >
            <Input placeholder="https://api.openai.com/v1" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="completion_dialect" label="对话API方言">
                <Input placeholder="openai" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="embedding_dialect" label="嵌入API方言">
                <Input placeholder="openai" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="rerank_dialect" label="重排API方言">
                <Input placeholder="jina_ai" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="allow_custom_base_url" valuePropName="checked" label="允许自定义基础URL">
            <Switch />
          </Form.Item>

          <Form.Item name="extra" label="额外配置 (JSON)">
            <Input.TextArea placeholder='{"key": "value"}' rows={3} />
          </Form.Item>
        </Form>
      </Modal>

      {/* Model Modal */}
      <Modal
        title={editingModel ? '编辑模型' : '添加模型'}
        open={modelModalVisible}
        onCancel={() => setModelModalVisible(false)}
        onOk={handleSaveModel}
        width={600}
        confirmLoading={loading}
      >
        <Form form={modelForm} layout="vertical" style={{ marginTop: 16 }}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="provider_name"
                label="提供商"
                rules={[{ required: true, message: '请选择提供商' }]}
              >
                <Select
                  placeholder="选择提供商"
                  disabled={!!editingModel}
                  onChange={(value) => {
                    const api = modelForm.getFieldValue('api');
                    if (api) {
                      handleApiTypeChange(api);
                    }
                  }}
                >
                  {configuration.providers.map(provider => (
                    <Select.Option key={provider.name} value={provider.name}>
                      {provider.label}
                    </Select.Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="api"
                label="API类型"
                rules={[{ required: true, message: '请选择API类型' }]}
              >
                <Select
                  placeholder="选择API类型"
                  disabled={!!editingModel}
                  onChange={handleApiTypeChange}
                >
                  <Select.Option value="completion">Completion</Select.Option>
                  <Select.Option value="embedding">Embedding</Select.Option>
                  <Select.Option value="rerank">Rerank</Select.Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="model"
                label="模型名称"
                rules={[{ required: true, message: '请输入模型名称' }]}
              >
                <Input placeholder="例如: gpt-4o-mini" disabled={!!editingModel} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="custom_llm_provider"
                label="自定义LLM提供商"
                rules={[{ required: true, message: '请输入自定义LLM提供商' }]}
              >
                <Input placeholder="自动填充" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="max_tokens" label="最大Token数">
                <InputNumber placeholder="4096" min={1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="tags" label="标签">
                <Select
                  mode="tags"
                  placeholder="输入标签"
                  tokenSeparators={[',']}
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>
    </PageContainer>
  );
}; 