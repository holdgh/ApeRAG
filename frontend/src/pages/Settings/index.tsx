import ChatRobot from '@/assets/chatbot.png';
import CheckedCard from '@/components/CheckedCard';
import { RobotOutlined } from '@ant-design/icons';
import { PageContainer } from '@ant-design/pro-components';
import { Avatar, Button, Card, Form, theme } from 'antd';
import { useEffect } from 'react';

export default () => {
  const [form] = Form.useForm();
  const onFinish = () => {};
  const { token } = theme.useToken();

  useEffect(() => {
    form.setFieldValue('model', 'GPT-3.5');
  }, []);

  return (
    <PageContainer ghost>
      <Card bordered={false}>
        <Form onFinish={onFinish} size="large" form={form} layout="vertical">
          <Form.Item name="image" label="Image">
            <Avatar
              size={60}
              src={ChatRobot}
              style={{ background: token.volcano5 }}
            >
              <RobotOutlined style={{ fontSize: 24 }} />
            </Avatar>
          </Form.Item>

          <Form.Item
            name="model"
            label="Select model"
            rules={[
              {
                required: true,
                message: 'type is required.',
              },
            ]}
          >
            <CheckedCard
              disabled
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
            <Button disabled type="primary" htmlType="submit">
              Update Bot
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </PageContainer>
  );
};
