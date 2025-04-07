import { Row, Col, Form, Input, Button, Typography } from 'antd';
import { MinusCircleOutlined, PlusOutlined } from '@ant-design/icons';

export default (formatMessage)=>(
  <>
    <Form.Item
      name={['config', 'region']}
      rules={[
        {
          required: true,
          message: 'Endpoint' + formatMessage({id:"msg.required"}),
        },
      ]}
      label={formatMessage({id:"text.endpoint"})}
    >
      <Input placeholder="Endpoint" />
    </Form.Item>
    <Form.Item
      label={formatMessage({id:"text.authorize"})}
      style={{ marginBottom: 0 }}
      required
    >
      <Row gutter={[8, 0]}>
        <Col span={12}>
          <Form.Item
            name={['config', 'access_key_id']}
            rules={[
              {
                required: true,
                message: 'Access Key' + formatMessage({id:"msg.required"}),
              },
            ]}
          >
            <Input.Password placeholder="Access Key" />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item
            name={['config', 'secret_access_key']}
            rules={[
              {
                required: true,
                message: 'Secret Access Key' + formatMessage({id:"msg.required"}),
              },
            ]}
          >
            <Input.Password placeholder="Secret Access Key" />
          </Form.Item>
        </Col>
      </Row>
    </Form.Item>
    
    <Form.Item
      label={formatMessage({id:"text.bucket"})}
      style={{ marginBottom: 0 }}
      required
    >
    <Form.List
      label={formatMessage({id:"text.bucket"})}
      name={['config', 'buckets']}
      initialValue={[{}]}
      style={{ marginBottom: 0 }}
      required
    >
    {(fields, { add, remove }) => (
      <>
      {fields.map(({ key, name, ...restField }) => (
        <Row key={key} gutter={[8, 0]}>
          <Col span={11}>
            <Form.Item
              name={[name, 'bucket']}
              rules={[
                {
                  required: true,
                  message: 'bucket' + formatMessage({id:"msg.required"}),
                },
              ]}
            >
              <Input placeholder="Bucket" />
            </Form.Item>
          </Col>
          <Col span={11}>
            <Form.Item name={[name, 'dir']}>
              <Input placeholder="Directory" />
            </Form.Item>
          </Col>
          <Col span="2">
            <Button
              onClick={() => remove(name)}
              block
              style={{ padding: '4px', textAlign: 'center' }}
            >
              <Typography.Text type="secondary">
                <MinusCircleOutlined />
              </Typography.Text>
            </Button>
          </Col>
        </Row>
      ))}
        <br />
        <Button
          type="dashed"
          onClick={() => add()}
          block
          icon={
            <Typography.Text type="secondary">
              <PlusOutlined /> {formatMessage({id:"text.bucket"})}
            </Typography.Text>
          }
        />
      </>
    )}
    </Form.List>
    </Form.Item>
  </>
);
