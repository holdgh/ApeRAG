import { Col, Form, Input, InputNumber, Row } from 'antd';

export default (
  <>
    <Row gutter={[12, 0]}>
      <Col span={16}>
        <Form.Item
          name="config.host"
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
      </Col>
      <Col span={8}>
        <Form.Item
          name="config.port"
          rules={[
            {
              required: true,
              message: 'port is required.',
            },
          ]}
          label="Port"
        >
          <InputNumber style={{ width: '100%' }} placeholder="port" />
        </Form.Item>
      </Col>
    </Row>
    <Row gutter={[12, 0]}>
      <Col span={12}>
        <Form.Item
          name="config.username"
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
      </Col>
      <Col span={12}>
        <Form.Item
          name="config.password"
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
      </Col>
    </Row>
    <Form.Item
      name="config.path"
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
  </>
);
