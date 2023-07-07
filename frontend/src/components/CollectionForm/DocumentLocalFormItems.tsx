import { Form, Input } from 'antd';

export default (
  <Form.Item
    name="config.path"
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
