import type { TypesDocumentConfig } from '@/types';
import { Col, Descriptions, Form, Input, InputNumber, Row } from 'antd';

export const getCloudDescItems = (config: TypesDocumentConfig) => {
  return (
    <>
      <Descriptions.Item label="Region">
        {config.region || ''}
      </Descriptions.Item>
      <Descriptions.Item label="Access Key">
        {config.access_key_id || ''}
      </Descriptions.Item>
      <Descriptions.Item label="Secret Access Key">
        {config.secret_access_key || ''}
      </Descriptions.Item>
      <Descriptions.Item label="Bucket">
        {config.bucket || ''}
      </Descriptions.Item>
      <Descriptions.Item label="Directory">
        {config.dir || ''}
      </Descriptions.Item>
    </>
  );
};
export const getCloudFormItems = () => {
  return (
    <>
      <Form.Item
        name="region"
        rules={[
          {
            required: true,
            message: 'region is required.',
          },
        ]}
        label="Region"
      >
        <Input />
      </Form.Item>
      <Form.Item
        name="access_key_id"
        rules={[
          {
            required: true,
            message: 'Access Key is required.',
          },
        ]}
        label="Access Key"
      >
        <Input.Password />
      </Form.Item>
      <Form.Item
        name="secret_access_key"
        rules={[
          {
            required: true,
            message: 'Secret Access Key is required.',
          },
        ]}
        label="Secret Access Key"
      >
        <Input.Password />
      </Form.Item>
      <Form.Item
        name="bucket"
        rules={[
          {
            required: true,
            message: 'bucket is required.',
          },
        ]}
        label="Bucket"
      >
        <Input />
      </Form.Item>
      <Form.Item name="dir" label="Directory">
        <Input />
      </Form.Item>
    </>
  );
};

export const getFtpDescItems = (config: TypesDocumentConfig) => {
  return (
    <>
      <Descriptions.Item label="Host">{config.host || ''}</Descriptions.Item>
      <Descriptions.Item label="Path">{config.path || ''}</Descriptions.Item>
      <Descriptions.Item label="Username">
        {config.username || ''}
      </Descriptions.Item>
      <Descriptions.Item label="Password">
        {config.password || ''}
      </Descriptions.Item>
    </>
  );
};
export const getFtpFormItems = () => {
  return (
    <>
      <Form.Item
        name="host"
        rules={[
          {
            required: true,
            message: 'host is required.',
          },
        ]}
        label="Host"
      >
        <Input />
      </Form.Item>
      <Form.Item
        name="path"
        rules={[
          {
            required: true,
            message: 'path is required.',
          },
        ]}
        label="Path"
      >
        <Input />
      </Form.Item>
      <Form.Item
        name="username"
        rules={[
          {
            required: true,
            message: 'username is required.',
          },
        ]}
        label="Username"
      >
        <Input />
      </Form.Item>
      <Form.Item
        name="password"
        rules={[
          {
            required: true,
            message: 'password is required.',
          },
        ]}
        label="Password"
      >
        <Input.Password />
      </Form.Item>
    </>
  );
};

export const getLocalDescItems = (config: TypesDocumentConfig) => {
  return (
    <>
      <Descriptions.Item label="Path">{config.path || ''}</Descriptions.Item>
    </>
  );
};
export const getLocalFormItems = () => {
  return (
    <Form.Item
      name="path"
      rules={[
        {
          required: true,
          message: 'local path is required.',
        },
      ]}
      label="Path"
    >
      <Input />
    </Form.Item>
  );
};

export const getEmailDescItems = (config: TypesDocumentConfig) => {
  return (
    <>
      <Descriptions.Item label="Server">
        {config.pop_server || ''}
      </Descriptions.Item>
      <Descriptions.Item label="Port">{config.port || ''}</Descriptions.Item>
      <Descriptions.Item label="Email">
        {config.email_address || ''}
      </Descriptions.Item>
      <Descriptions.Item label="Password">
        {config.email_password || ''}
      </Descriptions.Item>
    </>
  );
};
export const getEmailFormItems = () => {
  return (
    <>
      <Row gutter={[12, 0]}>
        <Col span={18}>
          <Form.Item
            name="pop_server"
            rules={[
              {
                required: true,
                message: 'server is required.',
              },
            ]}
            label="Server"
          >
            <Input />
          </Form.Item>
        </Col>
        <Col span={6}>
          <Form.Item
            name="port"
            rules={[
              {
                required: true,
                message: 'port is required.',
              },
            ]}
            label="Port"
          >
            <InputNumber style={{ width: '100%' }} />
          </Form.Item>
        </Col>
      </Row>

      <Form.Item
        name="email_address"
        rules={[
          {
            required: true,
            message: 'email is required.',
          },
          {
            type: 'email',
          },
        ]}
        label="Email"
      >
        <Input />
      </Form.Item>
      <Form.Item
        name="email_password"
        rules={[
          {
            required: true,
            message: 'password is required.',
          },
        ]}
        label="Password"
      >
        <Input.Password />
      </Form.Item>
    </>
  );
};
