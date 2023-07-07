import { DATABASE_TYPE_OPTIONS } from '@/constants';
import { Col, Form, Input, InputNumber, Radio, Row } from 'antd';

export default (
  <>
    <Form.Item
      name="config.db_type"
      rules={[
        {
          required: true,
          message: 'database is required.',
        },
      ]}
      label="Database Type"
    >
      <Radio.Group options={DATABASE_TYPE_OPTIONS} />
    </Form.Item>
    <Row gutter={[12, 0]}>
      <Col span={12}>
        <Form.Item
          name="config.host"
          label="Host"
          rules={[
            {
              required: true,
              message: 'host is required.',
            },
          ]}
        >
          <Input placeholder="host" />
        </Form.Item>
      </Col>
      <Col span={4}>
        <Form.Item name="config.port" label="Port">
          <InputNumber style={{ width: '100%' }} placeholder="port" />
        </Form.Item>
      </Col>
      <Col span={8}>
        <Form.Item
          name="config.db_name"
          label="Database"
          rules={[
            {
              required: true,
              message: 'database name is required.',
            },
          ]}
        >
          <Input placeholder="database" />
        </Form.Item>
      </Col>
    </Row>

    <Row gutter={[12, 0]}>
      <Col span={12}>
        <Form.Item name="config.username" label="Username">
          <Input placeholder="username" />
        </Form.Item>
      </Col>
      <Col span={12}>
        <Form.Item name="config.password" label="Password">
          <Input.Password placeholder="password" />
        </Form.Item>
      </Col>
    </Row>

    <Form.Item name="config.verify" label="SSL">
      <Radio.Group>
        <Radio value="prefered">Prefered</Radio>
        <Radio value="ca_only">CA only</Radio>
        <Radio value="full">Full</Radio>
      </Radio.Group>
    </Form.Item>
  </>
);
