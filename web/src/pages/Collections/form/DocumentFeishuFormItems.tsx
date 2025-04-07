import { Col, Form, Input, Row } from 'antd';

export default (formatMessage)=>(
  <>
    <Form.Item
      label={formatMessage({id:"text.authorize"})}
      style={{ marginBottom: 0 }}
      required
    >
      <Row gutter={[8, 0]}>
        <Col span={12}>
          <Form.Item
            name={['config', 'app_id']}
            rules={[
              {
                required: true,
                message: formatMessage({id:"text.app_id.help"}),
              },
            ]}
          >
            <Input.Password placeholder="Feishu App ID" />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item
            name={['config', 'app_secret']}
            rules={[
              {
                required: true,
                message: formatMessage({id:"text.app_secret.help"}),
              },
            ]}
          >
            <Input.Password placeholder="Feishu App Secret" />
          </Form.Item>
        </Col>
      </Row>
    </Form.Item>

    <Form.Item
      label={formatMessage({id:"text.doc_space"})}
      style={{ marginBottom: 0 }}
      required
    >
      <Row gutter={[8, 0]}>
        <Col span={12}>
          <Form.Item
            name={['config', 'space_id']}
            rules={[
              {
                required: true,
                message: 'Space ID' + formatMessage({id:"msg.required"}),
              },
            ]}
            required
          >
            <Input placeholder="Feishu Doc Space ID" />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item
            name={['config', 'node_id']}
            rules={[
              {
                required: true,
                message: 'Node ID' + formatMessage({id:"msg.required"}),
              },
            ]}
            required
          >
            <Input placeholder="Feishu Doc Node ID" />
          </Form.Item>
        </Col>
      </Row>
    </Form.Item>
  </>
);
