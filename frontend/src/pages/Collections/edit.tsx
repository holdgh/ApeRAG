import CheckedCard from '@/components/CheckedCard';
import { Collection } from '@/models/collection';
import { ReadCollection, UpdateCollection } from '@/services/collections';
import { SnippetsOutlined, VideoCameraOutlined } from '@ant-design/icons';
import { useParams } from '@umijs/max';
import { App, Button, Card, Form, Input } from 'antd';
import { useEffect, useState } from 'react';

export default () => {
  const [collection, setCollection] = useState<Collection>();
  const [form] = Form.useForm();
  const { collectionId } = useParams();
  const { message } = App.useApp();

  const getCollection = async () => {
    if (!collectionId) return;
    const { data } = await ReadCollection(collectionId);
    setCollection(data);
    form.setFieldsValue(data);
  };

  const onFinish = async () => {
    if (!collectionId) return;
    const values = await form.getFieldsValue();
    const { data } = await UpdateCollection(collectionId, {
      ...collection,
      ...values,
    });
    if (data.id) message.success('update success');
  };

  useEffect(() => {
    getCollection();
  }, []);

  return (
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
            disabled
            options={[
              {
                icon: <SnippetsOutlined />,
                label: 'Document',
                value: 'Document',
                description: 'Use docx, pptx, csv, pdf, or md as a collection.',
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
            Update
          </Button>
        </Form.Item>
      </Form>
    </Card>
  );
};
