import { Col, Form, Input, Row } from 'antd';

export default (
  <>
    <Row gutter={[12, 0]}>
      <Col span={12}>
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
      <Col span={12}>
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
  </>
);
