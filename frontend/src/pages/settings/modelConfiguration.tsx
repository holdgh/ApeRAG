import { PageContainer, PageHeader } from '@/components';
import { api } from '@/services';
import { LlmConfigurationResponse, LlmProvider, LlmProviderModel } from '@/api';
import { DeleteOutlined, EditOutlined, PlusOutlined, ArrowLeftOutlined, SettingOutlined } from '@ant-design/icons';
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
  Space,
} from 'antd';
import { useCallback, useEffect, useState } from 'react';
import { useIntl, useModel } from 'umi';

const { Title } = Typography;

// 弹窗内容视图类型
type ModalViewType = 'list' | 'add' | 'edit';

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

  // Model management modal state
  const [modelManagementVisible, setModelManagementVisible] = useState(false);
  const [currentProvider, setCurrentProvider] = useState<LlmProvider | null>(null);
  const [modalView, setModalView] = useState<ModalViewType>('list');
  const [modelForm] = Form.useForm();
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
        await api.llmProvidersProviderNamePut({
          providerName: editingProvider.name,
          llmProviderUpdate: values,
        });
        message.success('Provider updated successfully');
      } else {
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

  // Model management operations
  const handleManageModels = useCallback((provider: LlmProvider) => {
    setCurrentProvider(provider);
    setModalView('list');
    setModelManagementVisible(true);
  }, []);

  const handleAddModel = useCallback(() => {
    setEditingModel(null);
    modelForm.resetFields();
    if (currentProvider) {
      modelForm.setFieldValue('provider_name', currentProvider.name);
    }
    setModalView('add');
  }, [modelForm, currentProvider]);

  const handleEditModel = useCallback((model: LlmProviderModel) => {
    setEditingModel(model);
    modelForm.setFieldsValue(model);
    setModalView('edit');
  }, [modelForm]);

  const handleSaveModel = useCallback(async () => {
    try {
      const values = await modelForm.validateFields();
      setLoading(true);

      if (editingModel) {
        await api.llmProvidersProviderNameModelsApiModelPut({
          providerName: editingModel.provider_name,
          api: editingModel.api as any,
          model: editingModel.model,
          llmProviderModelUpdate: values,
        });
        message.success('Model updated successfully');
      } else {
        await api.llmProvidersProviderNameModelsPost({
          providerName: values.provider_name,
          llmProviderModelCreate: values,
        });
        message.success('Model created successfully');
      }

      setModalView('list');
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

  const handleBackToList = useCallback(() => {
    setModalView('list');
    setEditingModel(null);
    modelForm.resetFields();
  }, [modelForm]);

  const handleCloseModelManagement = useCallback(() => {
    setModelManagementVisible(false);
    setModalView('list');
    setCurrentProvider(null);
    setEditingModel(null);
    modelForm.resetFields();
  }, [modelForm]);

  // Handle API type change to auto-fill custom_llm_provider
  const handleApiTypeChange = useCallback((api: string) => {
    if (currentProvider) {
      let dialect = '';
      switch (api) {
        case 'completion':
          dialect = currentProvider.completion_dialect || 'openai';
          break;
        case 'embedding':
          dialect = currentProvider.embedding_dialect || 'openai';
          break;
        case 'rerank':
          dialect = currentProvider.rerank_dialect || 'jina_ai';
          break;
      }
      modelForm.setFieldValue('custom_llm_provider', dialect);
    }
  }, [modelForm, currentProvider]);

  // Get models for current provider
  const getCurrentProviderModels = useCallback(() => {
    if (!currentProvider) return [];
    return configuration.models.filter(model => model.provider_name === currentProvider.name);
  }, [configuration.models, currentProvider]);

  // Get model count for provider
  const getProviderModelCount = useCallback((providerName: string) => {
    return configuration.models.filter(model => model.provider_name === providerName).length;
  }, [configuration.models]);

  // Provider table columns
  const providerColumns: TableProps<LlmProvider>['columns'] = [
    {
      title: '服务商ID',
      dataIndex: 'name',
      key: 'name',
      width: 120,
    },
    {
      title: '显示名称',
      dataIndex: 'label',
      key: 'label',
      width: 150,
    },
    {
      title: 'API基础URL',
      dataIndex: 'base_url',
      key: 'base_url',
      ellipsis: true,
    },
    {
      title: '模型数量',
      key: 'model_count',
      width: 100,
      render: (_, record) => (
        <span>{getProviderModelCount(record.name)}</span>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 200,
      render: (_, record) => (
        <Space>
          <Button
            type="primary"
            size="small"
            icon={<SettingOutlined />}
            onClick={() => handleManageModels(record)}
          >
            管理模型
          </Button>
          <Button
            type="text"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEditProvider(record)}
          >
            编辑
          </Button>
          <Button
            type="text"
            size="small"
            icon={<DeleteOutlined />}
            danger
            onClick={() => handleDeleteProvider(record)}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ];

  // Model table columns for modal
  const modalModelColumns: TableProps<LlmProviderModel>['columns'] = [
    {
      title: 'API类型',
      dataIndex: 'api',
      key: 'api',
      width: 100,
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
      width: 150,
    },
    {
      title: '最大Token数',
      dataIndex: 'max_tokens',
      key: 'max_tokens',
      width: 120,
      render: (value?: number) => value || '-',
    },
    {
      title: '标签',
      dataIndex: 'tags',
      key: 'tags',
      width: 120,
      render: (tags: string[]) => (
        <>
          {tags?.map(tag => (
            <Tag key={tag}>{tag}</Tag>
          ))}
        </>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 120,
      render: (_, record) => (
        <Space>
          <Button
            type="text"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEditModel(record)}
          >
            编辑
          </Button>
          <Button
            type="text"
            size="small"
            icon={<DeleteOutlined />}
            danger
            onClick={() => handleDeleteModel(record)}
          >
            删除
          </Button>
        </Space>
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
      >
        <Table
          columns={providerColumns}
          dataSource={configuration.providers}
          rowKey="name"
          loading={loading}
          pagination={false}
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

      {/* Model Management Modal */}
      <Modal
        title={currentProvider ? `${currentProvider.label} - 模型管理` : '模型管理'}
        open={modelManagementVisible}
        onCancel={handleCloseModelManagement}
        footer={null}
        width={900}
        destroyOnClose
      >
        {modalView === 'list' && (
          <div>
            <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Title level={5} style={{ margin: 0 }}>模型列表</Title>
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={handleAddModel}
              >
                添加模型
              </Button>
            </div>
            <Table
              columns={modalModelColumns}
              dataSource={getCurrentProviderModels()}
              rowKey={(record) => `${record.api}-${record.model}`}
              loading={loading}
              pagination={false}
              size="small"
            />
          </div>
        )}

        {(modalView === 'add' || modalView === 'edit') && (
          <div>
            <div style={{ marginBottom: 16, display: 'flex', alignItems: 'center' }}>
              <Button
                type="text"
                icon={<ArrowLeftOutlined />}
                onClick={handleBackToList}
                style={{ marginRight: 8 }}
              >
                返回列表
              </Button>
              <Title level={5} style={{ margin: 0 }}>
                {modalView === 'add' ? '添加新模型' : `编辑模型：${editingModel?.model}`}
              </Title>
            </div>

            <Form form={modelForm} layout="vertical" onFinish={handleSaveModel}>
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    name="provider_name"
                    label="提供商"
                    rules={[{ required: true, message: '请选择提供商' }]}
                  >
                    <Select
                      placeholder="选择提供商"
                      disabled
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

              <div style={{ marginTop: 24, display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
                <Button onClick={handleBackToList}>
                  取消
                </Button>
                <Button type="primary" htmlType="submit" loading={loading}>
                  保存
                </Button>
              </div>
            </Form>
          </div>
        )}
      </Modal>
    </PageContainer>
  );
}; 