import CheckedCard from '@/components/CheckedCard';
import { CreateCollection } from '@/services/collections';
import { SnippetsOutlined, VideoCameraOutlined } from '@ant-design/icons';
import { PageContainer } from '@ant-design/pro-components';
import { history } from '@umijs/max';
import { App, Button, Card, Form, Input } from 'antd';
import { useEffect } from 'react';

export default () => {
  const [form] = Form.useForm();
  const { message } = App.useApp();

  const onFinish = async () => {
    const values = await form.getFieldsValue();
    const { data } = await CreateCollection(values);
    if (data.id) message.success('create success');
    history.push(`/collections/${data.id}/documents`);
  };

  useEffect(() => {
    form.setFieldValue('type', 'Document');
  }, []);

  return (
    <PageContainer ghost>
      <Card bordered={false}>
        <Form onFinish={onFinish} size="large" form={form} layout="vertical">
          <Form.Item
            name="title"
            label="Title"
            rules={[
              {
                required: true,
                message: 'title is required.',
              },
            ]}
          >
            <Input />
          </Form.Item>
          <Form.Item name="description" label="Description">
            <Input.TextArea rows={4} />
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
                  icon: <SnippetsOutlined />,
                  label: 'Document',
                  value: 'Document',
                  description:
                    'Use docx, pptx, csv, pdf, or md as a collection.',
                },
                {
                  icon: <VideoCameraOutlined />,
                  label: 'Multimedia',
                  value: 'Multimedia',
                  description: 'Use audio or video as a collection.',
                },
              ]}
            />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit">
              Create
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </PageContainer>
  );
};
