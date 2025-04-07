import { Form, Input } from 'antd';

export default (formatMessage)=>(
<>
  <Form.Item
    name={['config', 'github', 'repo']}
    rules={[
      {
        required: true,
        message: formatMessage({id:"text.repo"}) + formatMessage({id:"msg.required"}),
      },
    ]}
    label={formatMessage({id:"text.repo"})}
  >
    <Input />
  </Form.Item>
  <Form.Item
    name={['config', 'github', 'branch']}
    rules={[
      {
        required: true,
        message: formatMessage({id:"text.branch"}) + formatMessage({id:"msg.required"}),
      },
    ]}
    label={formatMessage({id:"text.branch"})}
  >
    <Input />
  </Form.Item>
  <Form.Item
    name={['config', 'github', 'path']}
    rules={[
      {
        required: true,
        message: formatMessage({id:"text.path"}) + formatMessage({id:"msg.required"}),
      },
    ]}
    label={formatMessage({id:"text.path"})}
  >
    <Input />
  </Form.Item>
</>
);
