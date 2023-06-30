import CheckedCard from '@/components/CheckedCard';
import CollectionConfig from '@/components/CollectionConfig';
import { CollectionType } from '@/models/collection';
import { AppstoreOutlined, ReadOutlined } from '@ant-design/icons';
import { Button, Form, FormInstance, Input } from 'antd';
import { useEffect, useState } from 'react';

type Props = {
  action: 'add' | 'edit';
  type: CollectionType;
  onFinish: () => void;
  form: FormInstance;
};

export default ({ onFinish, form, action, type }: Props) => {
  const [collectionType, setCollectionType] = useState<CollectionType>();

  useEffect(() => {
    setCollectionType(type);
  }, [type]);

  return (
    <Form onFinish={onFinish} size="large" form={form} layout="vertical">
      <Form.Item
        name="title"
        label="Title"
        rules={[
          {
            required: true,
            message: 'Title is required.',
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
            message: 'Type is required.',
          },
        ]}
      >
        <CheckedCard
          disabled={action === 'edit'}
          onChange={(v) => setCollectionType(v as CollectionType)}
          options={[
            {
              icon: <ReadOutlined />,
              label: 'Document',
              value: 'document',
              description: 'Use docx, pptx, csv, pdf, or md as a collection.',
            },
            {
              icon: <AppstoreOutlined />,
              label: 'Database',
              value: 'database',
              description: 'Use database as a collection.',
            },
          ]}
        />
      </Form.Item>

      {collectionType === 'database' ? (
        <Form.Item
          name="config"
          rules={[
            {
              required: true,
              message: 'Database connection is required.',
            },
          ]}
        >
          <CollectionConfig />
        </Form.Item>
      ) : null}

      <Form.Item>
        <Button type="primary" htmlType="submit">
          {action === 'add' ? 'Create' : 'Save'}
        </Button>
      </Form.Item>
    </Form>
  );
};
