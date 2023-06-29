import { CollectionConfig, CollectionConfigCerify, collectionConfigDBTypeOptions } from '@/models/collection';
import { useEffect, useState } from 'react';

import { getUser } from '@/models/user';
import { TestCollection } from '@/services/collections';
import {
  ApiOutlined,
  CheckOutlined,
  EditOutlined,
  UploadOutlined,
} from '@ant-design/icons';
import {
  App,
  Button,
  Col,
  Descriptions,
  Divider,
  Form,
  Input,
  InputNumber,
  Modal,
  Radio,
  Row,
  Select,
  Space,
  Typography,
  Upload,
  UploadProps,
  theme,
} from 'antd';

type PropsType = {
  value?: string;
  onChange?: (str: string) => void;
  disabled?: boolean;
};

export default ({ value = '', onChange = () => {}, disabled }: PropsType) => {
  const [valid, setValid] = useState<boolean>(false);
  const [visible, setVisible] = useState<boolean>(false);
  const { message } = App.useApp();
  const [form] = Form.useForm();
  const { token } = theme.useToken();
  const user = getUser();
  const [config, setConfig] = useState<CollectionConfig>({
    host: '',
    verify: 'prefered',
  });

  const onConnectTest = async () => {
    const values = await form.validateFields();
    const { data } = await TestCollection(values);
    if (data) {
      setValid(true);
    } else {
      message.error('connect error');
    }
  };

  const onSave = async () => {
    const values = await form.getFieldsValue();
    onChange(JSON.stringify(values));
    setConfig(values);
    setVisible(false);
  };

  const footer = (
    <Space>
      {valid ? (
        <Typography.Text type="success">
          <CheckOutlined /> connection success!
        </Typography.Text>
      ) : (
        <Typography.Link onClick={onConnectTest}>
          <ApiOutlined /> Connection Test
        </Typography.Link>
      )}
      <Divider type="vertical" />
      <Button onClick={() => setVisible(false)}>Cancel</Button>
      <Button type="primary" disabled={!valid} onClick={onSave}>
        Save
      </Button>
    </Space>
  );

  const renderUpload = (type: 'ca_cert' | 'client_key' | 'client_cert') => {
    const uploadProps: UploadProps = {
      name: 'file',
      multiple: false,
      showUploadList: false,
      action: `/api/v1/collections/ca/upload`,
      headers: {
        Authorization: 'Bearer ' + user?.__raw,
      },
      onChange(info) {
        const { status } = info.file;
        if (status === 'done') {
          form.setFieldValue(type, info?.file?.response?.data || '');
        } else if (status === 'error') {
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
    let defaultConfig: CollectionConfig = config;
    try {
      defaultConfig = { ...defaultConfig, ...JSON.parse(value) };
    } catch (err) {}
    form.setFieldsValue(defaultConfig);
    setConfig(defaultConfig);
  }, []);

  return (
    <>
      <Descriptions
        title={<Typography.Text>Database Connection</Typography.Text>}
        size="small"
        bordered
        column={{ xs: 1, sm: 2, md: 2 }}
        contentStyle={{
          color: token.colorTextDisabled,
          minWidth: 100,
        }}
        extra={
          <Typography.Link
            onClick={() => {
              if (!disabled) setVisible(true);
            }}
          >
            <EditOutlined />
          </Typography.Link>
        }
      >
        <Descriptions.Item label="Database Type">
          {config.db_type || ''}
        </Descriptions.Item>
        <Descriptions.Item label="Database">
          {config.db_name || ''}
        </Descriptions.Item>
        <Descriptions.Item label="Host">{config.host || ''}</Descriptions.Item>
        <Descriptions.Item label="Port">{config.port || ''}</Descriptions.Item>
        <Descriptions.Item label="Username">
          {config.username || ''}
        </Descriptions.Item>
        <Descriptions.Item label="Password">
          <Input.Password
            disabled
            visibilityToggle={false}
            bordered={false}
            value={config.password}
          />
        </Descriptions.Item>
        <Descriptions.Item label="SSL">{config.verify}</Descriptions.Item>
      </Descriptions>

      <Modal
        title="Connection Config"
        open={visible}
        onCancel={() => setVisible(false)}
        footer={footer}
      >
        <Form onChange={() => setValid(false)} form={form} layout="vertical">
          <Form.Item
            name="db_type"
            rules={[
              {
                required: true,
                message: 'database type is required.',
              },
            ]}
            label="Database type"
          >
            <Select options={collectionConfigDBTypeOptions}/>
          </Form.Item>
          <Row gutter={[12, 0]}>
            <Col span={16}>
              <Form.Item
                name="host"
                label="Host"
                rules={[
                  {
                    required: true,
                    message: 'host is required.',
                  },
                ]}
              >
                <Input placeholder="database host" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="port" label="Port">
                <InputNumber style={{ width: '100%' }} placeholder="port" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="db_name" label="Database name">
            <Input />
          </Form.Item>

          <Form.Item name="username" label="Username">
            <Input />
          </Form.Item>
          <Form.Item name="password" label="Password">
            <Input.Password />
          </Form.Item>

          <Form.Item name="verify" label="SSL">
            <Radio.Group
              onChange={(e) => {
                const value = e.target.value as CollectionConfigCerify;
                setConfig((s) => ({ ...s, verify: value }));
              }}
            >
              <Radio value="prefered">Prefered</Radio>
              <Radio value="ca_only">CA only</Radio>
              <Radio value="full">Full</Radio>
            </Radio.Group>
          </Form.Item>

          {config.verify && config.verify !== 'prefered' ? (
            <Form.Item
              name="ca_cert"
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
                addonAfter={renderUpload('ca_cert')}
              />
            </Form.Item>
          ) : null}

          {config.verify && config.verify === 'full' ? (
            <Form.Item
              name="client_key"
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
                addonAfter={renderUpload('client_key')}
              />
            </Form.Item>
          ) : null}

          {config.verify && config.verify === 'full' ? (
            <Form.Item
              name="client_cert"
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
                addonAfter={renderUpload('client_cert')}
              />
            </Form.Item>
          ) : null}
        </Form>
      </Modal>
    </>
  );
};
