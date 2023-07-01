import type { TypesDocumentConfig } from '@/models/collection';
import { Descriptions, Form, Input } from 'antd';

// desc
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

export const getFtpDescItems = (config: TypesDocumentConfig) => {
  return (
    <>
      <Descriptions.Item label="Host">{config.host || ''}</Descriptions.Item>
      <Descriptions.Item label="Username">
        {config.username || ''}
      </Descriptions.Item>
      <Descriptions.Item label="Password">
        {config.password || ''}
      </Descriptions.Item>
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

// form
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
