import { Form, Input } from 'antd';

export default (formatMessage)=>(
  <Form.Item
    name={['config', 'path']}
    rules={[
      {
        required: true,
        message: 'local path' + formatMessage({id:"msg.required"}),
      },
    ]}
    label={formatMessage({id:"text.path"})}
  >
    <Input />
  </Form.Item>
);
