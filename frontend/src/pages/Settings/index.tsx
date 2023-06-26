import CheckedCard from '@/components/CheckedCard';
import { PageContainer } from '@ant-design/pro-components';
import { Avatar, Button, Form } from 'antd';

export default () => {
  const [form] = Form.useForm();
  const onFinish = () => {};
  return (
    <PageContainer ghost>
      <Form onFinish={onFinish} size="large" form={form} layout="vertical">
        <Form.Item name="image" label="Image">
          <Avatar size={60} />
        </Form.Item>

        <Form.Item
          name="type"
          label="Type"
          rules={[
            {
              required: true,
              message: 'type is required.',
            },
          ]}
        >
          <CheckedCard
            options={[
              {
                label: 'GPT-3.5',
                value: 'GPT-3.5',
                description: 'Less acurate, but fast',
              },
              {
                label: 'GPT-4',
                value: 'GPT-4',
                description: 'Most acurate, but slow',
              },
            ]}
          />
        </Form.Item>
        <Form.Item>
          <Button type="primary" htmlType="submit">
            Update Bot
          </Button>
        </Form.Item>
      </Form>
    </PageContainer>
  );
};
