import { Collection } from '@/api';
import { ApeMarkdown, CheckCard } from '@/components';
import {
  COLLECTION_SOURCE,
  COLLECTION_SOURCE_EMAIL,
  MODEL_PROVIDER_ICON,
} from '@/constants';
import { api } from '@/services';
import { UndrawEmpty } from 'react-undraw-illustrations';

import { CollectionConfigSource, CollectionEmailSource } from '@/types';
import { getProviderByModelName } from '@/utils';
import { useRequest } from 'ahooks';
import {
  Alert,
  Avatar,
  Button,
  Card,
  Col,
  Divider,
  Form,
  FormInstance,
  Input,
  Radio,
  Row,
  Segmented,
  Select,
  Space,
  Switch,
  theme,
  Typography,
} from 'antd';
import _ from 'lodash';
import { useEffect, useMemo } from 'react';
import { FormattedMessage, useIntl } from 'umi';
import DocumentCloudFormItems from './DocumentCloudFormItems';
import DocumentEmailFormItems from './DocumentEmailFormItems';
import DocumentFeishuFormItems from './DocumentFeishuFormItems';
import DocumentFtpFormItems from './DocumentFtpFormItems';
import DocumentGithubFormItems from './DocumentGithubFormItems';
import DocumentLocalFormItems from './DocumentLocalFormItems';

type Props = {
  action: 'add' | 'edit';
  values?: Collection;
  form: FormInstance<Collection>;
  onSubmit: (data: Collection) => void;
};

const configSourceKey = ['config', 'source'];
const configSensitiveProtectKey = ['config', 'sensitive_protect'];

const configEmbeddingModelKey = ['config', 'embedding', 'model'];
const configEmbeddingModelServiceProviderKey = [
  'config',
  'embedding',
  'model_service_provider',
];
const configEmbeddingCustomLlmProviderKey = [
  'config',
  'embedding',
  'custom_llm_provider',
];

const configEnableKnowledgeGraphKey = ['config', 'enable_knowledge_graph'];

const configCompletionModelKey = ['config', 'completion', 'model'];
const configCompletionModelServiceProviderKey = [
  'config',
  'completion',
  'model_service_provider',
];
const configCompletionCustomLlmProviderKey = [
  'config',
  'completion',
  'custom_llm_provider',
];

const configEmailSourceKey = ['config', 'email_source'];

export default ({ onSubmit, action, values, form }: Props) => {
  const { data: availableModelsGetRes, loading } = useRequest(
    api.availableModelsGet,
  );
  const { formatMessage } = useIntl();
  const { token } = theme.useToken();

  const availableModels = useMemo(
    () => availableModelsGetRes?.data.items || [],
    [availableModelsGetRes],
  );

  // save collection
  const onFinish = async () => {
    const data = await form.validateFields();
    onSubmit(data);
  };

  // form field watch
  const source = Form.useWatch(configSourceKey, form);
  const emailSource: CollectionEmailSource | undefined = Form.useWatch(
    configEmailSourceKey,
    form,
  );
  const sensitiveProtect = Form.useWatch(configSensitiveProtectKey, form);
  const embeddingModel = Form.useWatch(configEmbeddingModelKey, form);
  const embeddingModelServiceProvider = Form.useWatch(
    configEmbeddingModelServiceProviderKey,
    form,
  );

  const enableKnowledgeGraph = Form.useWatch(
    configEnableKnowledgeGraphKey,
    form,
  );

  const completionModel = Form.useWatch(configCompletionModelKey, form);
  const completionModelServiceProvider = Form.useWatch(
    configCompletionModelServiceProviderKey,
    form,
  );

  // embedding model options
  const embeddingModelOptions = useMemo(
    () =>
      _.map(availableModels, (provider) => {
        return {
          label: (
            <Space>
              <Avatar
                size={24}
                shape="square"
                src={
                  provider.name ? MODEL_PROVIDER_ICON[provider.name] : undefined
                }
              />
              <span>{provider.label || provider.name}</span>
            </Space>
          ),
          options: provider.embedding?.map((item) => {
            return {
              label: item.model,
              value: item.model,
            };
          }),
        };
      }),
    [availableModels],
  );

  // completion model options
  const completionModelsOptions = useMemo(
    () =>
      _.map(availableModels, (provider) => {
        return {
          label: (
            <Space>
              <Avatar
                size={24}
                shape="square"
                src={
                  provider.name ? MODEL_PROVIDER_ICON[provider.name] : undefined
                }
              />
              <span>{provider.label || provider.name}</span>
            </Space>
          ),
          options: provider.completion?.map((item: any) => {
            return {
              label: item.model,
              value: item.model,
            };
          }),
        };
      }),
    [availableModels],
  );

  useEffect(() => {
    if (embeddingModel) {
      const { provider, model } = getProviderByModelName(
        embeddingModel,
        'embedding',
        availableModels,
      );
      form.setFieldValue(
        configEmbeddingModelServiceProviderKey,
        provider?.name,
      );
      form.setFieldValue(
        configEmbeddingCustomLlmProviderKey,
        model?.custom_llm_provider,
      );
    }
  }, [embeddingModel, availableModels]);

  useEffect(() => {
    if (completionModel) {
      const { provider, model } = getProviderByModelName(
        completionModel,
        'completion',
        availableModels,
      );
      form.setFieldValue(
        configCompletionModelServiceProviderKey,
        provider?.name,
      );
      form.setFieldValue(
        configCompletionCustomLlmProviderKey,
        model?.custom_llm_provider,
      );
    }
  }, [completionModel, availableModels]);

  useEffect(() => {
    if (source === 'ftp') {
      form.setFieldValue(['config', 'port'], 21);
    }
    if (source === 'email') {
      if (!emailSource) {
        form.setFieldValue(configEmailSourceKey, 'gmail');
      } else {
        form.setFieldValue(
          ['config', 'pop_server'],
          COLLECTION_SOURCE_EMAIL[emailSource].pop_server,
        );
        form.setFieldValue(
          ['config', 'port'],
          COLLECTION_SOURCE_EMAIL[emailSource].port,
        );
      }
    }
  }, [source, emailSource]);

  return (
    <Form
      autoComplete="off"
      onFinish={onFinish}
      layout="vertical"
      form={form}
      initialValues={values}
    >
      <Card style={{ marginBottom: 20 }}>
        <Form.Item
          name="title"
          label={formatMessage({ id: 'text.title' })}
          rules={[
            {
              required: true,
              message: formatMessage({ id: 'text.title.required' }),
            },
          ]}
        >
          <Input />
        </Form.Item>
        <Form.Item
          name="description"
          label={formatMessage({ id: 'text.description' })}
        >
          <Input.TextArea maxLength={300} rows={3} />
        </Form.Item>

        <Row gutter={24}>
          <Col
            {...{
              xs: 24,
              sm: 24,
              md: 12,
              lg: 12,
              xl: 12,
              xxl: 12,
            }}
          >
            <Form.Item
              name={configEmbeddingModelKey}
              rules={[
                {
                  required: true,
                  message: formatMessage({
                    id: 'collection.embedding_model.required',
                  }),
                },
              ]}
              className="form-item-wrap"
              label={formatMessage({ id: 'collection.embedding_model' })}
            >
              <Select
                options={embeddingModelOptions}
                disabled={action === 'edit'}
                labelRender={({ label, value }) => {
                  return (
                    <Space style={{ alignItems: 'center' }}>
                      <Avatar
                        size={24}
                        shape="square"
                        src={MODEL_PROVIDER_ICON[embeddingModelServiceProvider]}
                        style={{
                          transform: 'translateY(-1px)',
                        }}
                      />
                      {label || value}
                    </Space>
                  );
                }}
                notFoundContent={
                  <Space
                    direction="vertical"
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      marginBlock: 24,
                    }}
                  >
                    <UndrawEmpty
                      primaryColor={token.colorPrimary}
                      height="80px"
                    />
                    <Typography.Text type="secondary">
                      <FormattedMessage id="collection.embedding_model_not_found" />
                    </Typography.Text>
                  </Space>
                }
              />
            </Form.Item>

            <Form.Item name={configEmbeddingModelServiceProviderKey} hidden>
              <Input hidden />
            </Form.Item>
            <Form.Item name={configEmbeddingCustomLlmProviderKey} hidden>
              <Input hidden />
            </Form.Item>
          </Col>
          <Col
            {...{
              xs: 24,
              sm: 24,
              md: 12,
              lg: 12,
              xl: 12,
              xxl: 12,
            }}
          >
            <Form.Item
              label={formatMessage({ id: 'collection.enable_knowledge_graph' })}
              valuePropName="checked"
              name={configEnableKnowledgeGraphKey}
            >
              <Switch />
            </Form.Item>
          </Col>
        </Row>

        {enableKnowledgeGraph ? (
          <>
            <Form.Item
              label={formatMessage({
                id: 'collection.lightrag_model',
              })}
              name={configCompletionModelKey}
              required
              rules={[
                {
                  required: true,
                  message: formatMessage({
                    id: 'collection.lightrag_model.required',
                  }),
                },
              ]}
            >
              <Select
                options={completionModelsOptions}
                labelRender={({ label, value }) => {
                  return (
                    <Space style={{ alignItems: 'center' }}>
                      <Avatar
                        size={24}
                        shape="square"
                        src={
                          MODEL_PROVIDER_ICON[completionModelServiceProvider]
                        }
                        style={{
                          transform: 'translateY(-1px)',
                        }}
                      />
                      {label || value}
                    </Space>
                  );
                }}
                notFoundContent={
                  <Space
                    direction="vertical"
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      marginBlock: 24,
                    }}
                  >
                    <UndrawEmpty
                      primaryColor={token.colorPrimary}
                      height="80px"
                    />
                    <Typography.Text type="secondary">
                      <FormattedMessage id="collection.lightrag_model_not_found" />
                    </Typography.Text>
                  </Space>
                }
              />
            </Form.Item>
            <Form.Item name={configCompletionModelServiceProviderKey} hidden>
              <Input hidden />
            </Form.Item>
            <Form.Item name={configCompletionCustomLlmProviderKey} hidden>
              <Input hidden />
            </Form.Item>
          </>
        ) : null}

        <Form.Item
          label={
            <>
              <Typography.Text>
                {formatMessage({ id: 'collection.sensitive.protect' })}
              </Typography.Text>
              <Typography.Text type="secondary">
                （{formatMessage({ id: 'collection.sensitive.help' })}）
              </Typography.Text>
            </>
          }
          valuePropName="checked"
          name={configSensitiveProtectKey}
        >
          <Switch />
        </Form.Item>
        {sensitiveProtect ? (
          <>
            <Form.Item
              label={formatMessage({
                id: 'collection.sensitive.protect.method',
              })}
              name={['config', 'sensitive_protect_method']}
              required
              rules={[
                {
                  required: true,
                  message: formatMessage({
                    id: 'collection.sensitive.protect.method.required',
                  }),
                },
              ]}
            >
              <Radio.Group
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 12,
                }}
                options={[
                  {
                    label: formatMessage({
                      id: 'collection.sensitive.nostore',
                    }),
                    value: 'nostore',
                  },
                  {
                    label: formatMessage({
                      id: 'collection.sensitive.replace',
                    }),
                    value: 'replace',
                  },
                ]}
              />
            </Form.Item>
          </>
        ) : null}

        <Form.Item
          name={configSourceKey}
          required
          label={formatMessage({ id: 'collection.source' })}
          rules={[
            {
              required: true,
              message: formatMessage({ id: 'collection.source.required' }),
            },
          ]}
        >
          <CheckCard
            options={Object.keys(COLLECTION_SOURCE).map((key) => {
              const config = values?.config;
              return {
                label: formatMessage({ id: `collection.source.${key}` }),
                value: key,
                icon: COLLECTION_SOURCE[key as CollectionConfigSource].icon,
                disabled:
                  !COLLECTION_SOURCE[key as CollectionConfigSource].enabled ||
                  (action === 'edit' && key !== config?.source),
              };
            })}
          />
        </Form.Item>

        {source === 'local' ? <DocumentLocalFormItems /> : null}

        {source === 'email' ? (
          <>
            <Form.Item
              required
              label={formatMessage({ id: 'email.source' })}
              name={configEmailSourceKey}
            >
              <Segmented
                size="small"
                block
                options={_.map(COLLECTION_SOURCE_EMAIL, (conf, key) => ({
                  label: (
                    <Space style={{ padding: 10 }}>
                      <Avatar shape="square" src={conf.icon} size={24} />
                      <Typography.Text>
                        <FormattedMessage id={`email.${key}`} />
                      </Typography.Text>
                    </Space>
                  ),
                  value: key,
                }))}
              />
            </Form.Item>
            <DocumentEmailFormItems />
            {emailSource ? (
              <Form.Item label="">
                <Alert
                  message={formatMessage({
                    id: `email.${emailSource}.tips.title`,
                  })}
                  description={
                    <ApeMarkdown>
                      {formatMessage({
                        id: `email.${emailSource}.tips.description`,
                      })}
                    </ApeMarkdown>
                  }
                  type="info"
                  showIcon
                />
              </Form.Item>
            ) : null}
          </>
        ) : null}

        {source === 's3' || source === 'oss' ? (
          <DocumentCloudFormItems />
        ) : null}

        {source === 'ftp' ? <DocumentFtpFormItems /> : null}

        {source === 'feishu' ? <DocumentFeishuFormItems /> : null}

        {source === 'github' ? <DocumentGithubFormItems /> : null}

        <br />
        <Divider />
        <div style={{ textAlign: 'right' }}>
          <Button
            loading={loading}
            style={{ minWidth: 160 }}
            type="primary"
            htmlType="submit"
          >
            {formatMessage({ id: 'action.save' })}
          </Button>
        </div>
      </Card>
    </Form>
  );
};
