import { Col, Form, Input, InputNumber, Row } from 'antd';

export default (
  <>
    <Row gutter={[12, 0]}>
      <Col span={18}>
        <Form.Item
          name="config.pop_server"
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
          name="config.port"
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
    <Row gutter={[12, 0]}>
      <Col span={12}>
        <Form.Item
          name="config.email_address"
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
      </Col>
      <Col span={12}>
        <Form.Item
          name="config.email_password"
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
  </>
);
