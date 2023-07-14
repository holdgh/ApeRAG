import CheckedCard from '@/components/CheckedCard';
import {
  CODE_PROMOT_EXAMPLE,
  COLLECTION_MODEL_OPTIONS_CONFIG,
  DATABASE_TYPE_OPTIONS,
  DOCUMENT_SOURCE_OPTIONS,
} from '@/constants';
import { getUser } from '@/models/user';
import { TestCollection } from '@/services/collections';
import { TypesCollection, TypesDatabaseConfig } from '@/types';
import {
  ApiOutlined,
  LoadingOutlined,
  UploadOutlined,
} from '@ant-design/icons';
import { useModel } from '@umijs/max';
import {
  App,
  Button,
  Card,
  Col,
  Divider,
  Form,
  Input,
  Row,
  Space,
  Typography,
  Upload,
  UploadProps,
  theme,
} from 'antd';
import flat from 'flat';
import { useEffect, useState } from 'react';
import DatabaseBaseFormItems from './DatabaseBaseFormItems';
import DocumentCloudFormItems from './DocumentCloudFormItems';
import DocumentEmailFormItems from './DocumentEmailFormItems';
import DocumentFtpFormItems from './DocumentFtpFormItems';
import DocumentLocalFormItems from './DocumentLocalFormItems';

type Props = {
  action: 'add' | 'edit';
  values: TypesCollection;
  onSubmit: (data: TypesCollection) => void;
};

export default ({ onSubmit, action, values }: Props) => {
  const [testing, setTesting] = useState<boolean>(false);
  const [remoteValid, setRemoteValid] = useState<boolean>(
    values.type !== 'database',
  );
  const { collectionLoading, models } = useModel('collection');

  const { message } = App.useApp();
  const user = getUser();
  const { token } = theme.useToken();

  const [form] = Form.useForm();
  const source = Form.useWatch('config.source', form);
  const dbVerify = Form.useWatch('config.verify', form);

  const onFinish = async () => {
    const data = form.getFieldsValue();
    onSubmit({
      ...values,
      ...flat.unflatten(data),
    });
  };

  const onConnectTest = async () => {
    const values = await form.validateFields();
    const d: TypesCollection = flat.unflatten(values);
    const config = d.config as TypesDatabaseConfig;

    setTesting(true);
    const res = await TestCollection(config);
    if (res.code === '200') {
      setRemoteValid(true);
      message.success(res.data || 'successfully connected');
    } else {
      setRemoteValid(false);
      message.error(res.message || 'connected error');
    }
    setTesting(false);
  };

  const renderUpload = (
    type: 'config.ca_cert' | 'config.client_key' | 'config.client_cert',
  ) => {
    const uploadProps: UploadProps = {
      name: 'file',
      multiple: false,
      showUploadList: false,
      maxCount: 1,
      action: `${API_ENDPOINT}/api/v1/collections/ca/upload`,
      // accept: '.pem,.key,.crt,.csr',
      headers: {
        Authorization: 'Bearer ' + user?.__raw,
      },
      onChange(info) {
        const { status } = info.file;
        const code = info?.file?.response?.code;
        const msg = info?.file?.response?.message;
        if (status === 'done') {
          if (code !== '200' && msg) {
            message.error(info?.file?.response?.message);
          }
          form.setFieldValue(type, info?.file?.response?.data || '');
        }
        if (status === 'error') {
          message.error('upload error');
        }
      },
    };
    return (
      <Upload {...uploadProps}>
        <Button type="text" size="small" icon={<UploadOutlined />} />
      </Upload>
    );
  };

  useEffect(() => {
    form.setFieldsValue(flat.flatten(values));
  }, []);

  return (
    <Form
      onFinish={onFinish}
      size="large"
      form={form}
      layout="vertical"
      onValuesChange={() => {
        if (values.type === 'database') {
          setRemoteValid(false);
        }
      }}
    >
      <Form.Item
        name="title"
        label="Title"
        rules={[
          {
            required: true,
            message: 'Title is required.',
          },
        ]}
      >
        <Input disabled={values.type === 'code' && action === 'edit'} />
      </Form.Item>
      <Form.Item
        name="description"
        label="Description"
        required={values.type === 'code'}
      >
        <Input.TextArea
          rows={2}
          autoSize={{
            minRows: 3,
            maxRows: 6,
          }}
          disabled={values.type === 'code' && action === 'edit'}
          maxLength={300}
          required={values.type === 'code'}
          showCount
          style={{ resize: 'none' }}
        />
      </Form.Item>
      <Form.Item name="type" style={{ display: 'none' }} />

      {values.type === 'code' ? (
        <Form.Item label="Examples">
          <Row gutter={[24, 24]}>
            {CODE_PROMOT_EXAMPLE.map((item, key) => (
              <Col key={key} span="8">
                <Card
                  hoverable
                  bodyStyle={{ height: 160 }}
                  size="small"
                  onClick={() => {
                    if (action === 'edit') return;
                    form.setFieldValue('description', item.text);
                    form.setFieldValue('title', item.title);
                  }}
                  style={{
                    marginBottom: 12,
                    borderColor: token.colorBorderSecondary,
                    background: token.colorBorderBg,
                  }}
                >
                  <Typography.Text type="secondary">
                    {item.text}
                  </Typography.Text>
                </Card>
              </Col>
            ))}
          </Row>
        </Form.Item>
      ) : null}

      {['document', 'database'].includes(values.type) ? (
        <Form.Item
          name="config.model"
          rules={[
            {
              required: true,
              message: 'model is required.',
            },
          ]}
          label="Model"
        >
          <CheckedCard
            size="large"
            options={models.map((name) => ({
              label: name,
              value: name,
              icon: COLLECTION_MODEL_OPTIONS_CONFIG[name].icon,
              disabled: COLLECTION_MODEL_OPTIONS_CONFIG[name].disabled,
            }))}
          />
        </Form.Item>
      ) : null}

      {values.type === 'document' ? (
        <>
          <Form.Item
            name="config.source"
            rules={[
              {
                required: true,
                message: 'source is required.',
              },
            ]}
            label="Source"
          >
            <CheckedCard
              disabled={action === 'edit'}
              options={DOCUMENT_SOURCE_OPTIONS}
            />
          </Form.Item>

          {source === 'local' ? DocumentLocalFormItems : null}
          {source === 'email' ? DocumentEmailFormItems : null}
          {source === 's3' || source === 'oss' ? DocumentCloudFormItems : null}
          {source === 'ftp' ? DocumentFtpFormItems : null}
        </>
      ) : null}

      {values.type === 'database' ? (
        <>
          <Form.Item
            name="config.db_type"
            rules={[
              {
                required: true,
                message: 'database is required.',
              },
            ]}
            label="Database Type"
          >
            <CheckedCard
              disabled={action === 'edit'}
              options={DATABASE_TYPE_OPTIONS}
            />
          </Form.Item>
          {DatabaseBaseFormItems}

          {dbVerify && dbVerify !== 'prefered' ? (
            <Form.Item
              name="config.ca_cert"
              label="CA Certificate"
              rules={[
                {
                  required: true,
                  message: 'CA Certificate is required.',
                },
              ]}
            >
              <Input.Password
                visibilityToggle={false}
                disabled
                addonAfter={renderUpload('config.ca_cert')}
              />
            </Form.Item>
          ) : null}

          {dbVerify && dbVerify === 'full' ? (
            <>
              <Form.Item
                name="config.client_key"
                label="Client Key"
                rules={[
                  {
                    required: true,
                    message: 'Client Key is required.',
                  },
                ]}
              >
                <Input.Password
                  visibilityToggle={false}
                  disabled
                  addonAfter={renderUpload('config.client_key')}
                />
              </Form.Item>
              <Form.Item
                name="config.client_cert"
                label="Client Certificate"
                rules={[
                  {
                    required: true,
                    message: 'Client Certificate is required.',
                  },
                ]}
              >
                <Input.Password
                  visibilityToggle={false}
                  disabled
                  addonAfter={renderUpload('config.client_cert')}
                />
              </Form.Item>
            </>
          ) : null}
        </>
      ) : null}

      <Space split={<Divider type="vertical" />}>
        <Button
          loading={collectionLoading}
          disabled={!remoteValid}
          type="primary"
          htmlType="submit"
        >
          {action === 'add' ? 'Create' : 'Save'}
        </Button>

        {values.type === 'database' ? (
          <Typography.Link onClick={onConnectTest}>
            <Space>
              {testing ? <LoadingOutlined /> : <ApiOutlined />}
              Connection Test
            </Space>
          </Typography.Link>
        ) : null}
      </Space>
    </Form>
  );
};
