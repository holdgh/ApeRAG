import { Col, Form, Input, Row } from 'antd';

export default (
  <>
    <Form.Item
      name="config.region"
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
    <Row gutter={[12, 0]}>
      <Col span={12}>
        <Form.Item
          name="config.access_key_id"
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
      </Col>
      <Col span={12}>
        <Form.Item
          name="config.secret_access_key"
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
      </Col>
    </Row>
    <Row gutter={[12, 0]}>
      <Col span={12}>
        <Form.Item
          name="config.bucket"
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
      </Col>
      <Col span={12}>
        <Form.Item name="config.dir" label="Directory">
          <Input />
        </Form.Item>
      </Col>
    </Row>
  </>
);
