import {
  DATABASE_TYPE_OPTIONS,
  DatabaseConfig,
  DatabaseConfigCerify,
} from '@/models/collection';
import { getUser } from '@/models/user';
import { TestCollection } from '@/services/collections';
import {
  ApiOutlined,
  CheckOutlined,
  EditOutlined,
  SettingOutlined,
  UploadOutlined,
} from '@ant-design/icons';
import {
  App,
  Button,
  Card,
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
import _ from 'lodash';
import { useEffect, useState } from 'react';
import styles from './index.less';

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
  const [config, setConfig] = useState<DatabaseConfig>({
    host: '',
    verify: 'prefered',
  });

  const onConnectTest = async () => {
    const values = await form.validateFields();
    const res = await TestCollection(values);
    if (res.data) {
      setValid(true);
    }

    if (res.code !== '404') {
      message.error(res.message);
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
      maxCount: 1,
      action: `/api/v1/collections/ca/upload`,
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
    let defaultConfig: DatabaseConfig = config;
    try {
      defaultConfig = { ...defaultConfig, ...JSON.parse(value) };
    } catch (err) {}
    form.setFieldsValue(defaultConfig);
    setConfig(defaultConfig);
  }, []);

  const DatabaseEdit = (
    <Card
      className={styles.databaseEdit}
      onClick={() => {
        if (!disabled) setVisible(true);
      }}
    >
      <Typography.Text type="secondary">
        <EditOutlined /> Database Connection
      </Typography.Text>
    </Card>
  );

  const DatabaseInfo = (
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
          <SettingOutlined />
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
  );

  return (
    <>
      {_.isEmpty(config.host) ? DatabaseEdit : DatabaseInfo}
      <Modal
        title="Connection Config"
        open={visible}
        onCancel={() => setVisible(false)}
        footer={footer}
      >
        <br />
        <Form onChange={() => setValid(false)} form={form} layout="vertical">
          <Form.Item
            name="db_type"
            rules={[
              {
                required: true,
                message: 'database is required.',
              },
            ]}
            label="Database type"
          >
            <Select options={DATABASE_TYPE_OPTIONS} />
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
                <Input placeholder="host" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="port" label="Port">
                <InputNumber style={{ width: '100%' }} placeholder="port" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="db_name" label="Database name">
            <Input placeholder="database" />
          </Form.Item>

          <Form.Item name="username" label="Username">
            <Input placeholder="username" />
          </Form.Item>
          <Form.Item name="password" label="Password">
            <Input.Password placeholder="password" />
          </Form.Item>

          <Form.Item name="verify" label="SSL">
            <Radio.Group
              onChange={(e) => {
                const value = e.target.value as DatabaseConfigCerify;
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
