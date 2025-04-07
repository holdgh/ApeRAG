import { Col, Form, Input, InputNumber, Row } from 'antd';

export default (formatMessage)=>(
  <>
    <Form.Item
      label={formatMessage({id:"text.service_address"})}
      style={{ marginBottom: 0 }}
      required
    >
      <Row gutter={[8, 0]}>
        <Col span={12}>
          <Form.Item
            name={['config', 'pop_server']}
            rules={[
              {
                required: true,
                message: 'server' + formatMessage({id:"msg.required"}),
              },
            ]}
          >
            <Input placeholder="Server" />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item
            name={['config', 'port']}
            rules={[
              {
                required: true,
                message: 'port' + formatMessage({id:"msg.required"}),
              },
            ]}
          >
            <InputNumber style={{ width: '100%' }} placeholder="Port" />
          </Form.Item>
        </Col>
      </Row>
    </Form.Item>
    <Form.Item
      label={formatMessage({id:"text.authorize"})}
      style={{ marginBottom: 0 }}
      required
    >
      <Row gutter={[8, 0]}>
        <Col span={12}>
          <Form.Item
            name={['config', 'email_address']}
            rules={[
              {
                required: true,
                message: 'email' + formatMessage({id:"msg.required"}),
              },
              {
                type: 'email',
              },
            ]}
          >
            <Input placeholder="Email" />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item
            name={['config', 'email_password']}
            rules={[
              {
                required: true,
                message: 'password' + formatMessage({id:"msg.required"}),
              },
            ]}
          >
            <Input.Password placeholder="Password" />
          </Form.Item>
        </Col>
      </Row>
    </Form.Item>
  </>
);
