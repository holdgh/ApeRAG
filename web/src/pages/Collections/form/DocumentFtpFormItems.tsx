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
            name={['config', 'host']}
            rules={[
              {
                required: true,
                message: 'host' + formatMessage({id:"msg.required"}),
              },
            ]}
          >
            <Input placeholder="Host" />
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
            name={['config', 'username']}
            rules={[
              {
                required: true,
                message: 'username' + formatMessage({id:"msg.required"}),
              },
            ]}
          >
            <Input placeholder="Username" />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item
            name={['config', 'password']}
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
    <Form.Item
      name={['config', 'path']}
      rules={[
        {
          required: true,
          message: 'path' + formatMessage({id:"msg.required"}),
        },
      ]}
      label={formatMessage({id:"text.path"})}
    >
      <Input placeholder="Path" />
    </Form.Item>
  </>
);
