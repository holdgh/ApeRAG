import CheckedCard from '@/components/CheckedCard';
import DatabaseConfig from '@/components/DatabaseConfig';
import DocumentConfig from '@/components/DocumentConfig';
import type { TypesCollectionType } from '@/models/collection';
import { AppstoreOutlined, ReadOutlined } from '@ant-design/icons';
import { Button, Form, FormInstance, Input, Space } from 'antd';
import { useEffect, useState } from 'react';

type Props = {
  action: 'add' | 'edit';
  type: TypesCollectionType;
  onFinish: () => void;
  onValuesChange: (changedValues: any, allValues: any) => void;
  form: FormInstance;
};

export default ({
  onFinish,
  form,
  action,
  type,
  onValuesChange = () => {},
}: Props) => {
  const [collectionType, setCollectionType] = useState<TypesCollectionType>();

  useEffect(() => {
    setCollectionType(type);
  }, [type]);

  const collectionTypeOptions = [
    {
      icon: <ReadOutlined />,
      label: <Space>Document</Space>,
      value: 'document',
      description: 'Use docx, pptx, csv, pdf, or md as a collection.',
    },
    {
      icon: <AppstoreOutlined />,
      label: 'Database',
      value: 'database',
      description: 'Use database as a collection.',
    },
  ];

  return (
    <Form
      onValuesChange={onValuesChange}
      onFinish={onFinish}
      size="large"
      form={form}
      layout="vertical"
    >
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
        <Input.TextArea rows={2} />
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
          onChange={(v) => setCollectionType(v as TypesCollectionType)}
          options={collectionTypeOptions}
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
          <DatabaseConfig disabled={action === 'edit'} />
        </Form.Item>
      ) : null}

      {collectionType === 'document' ? (
        <Form.Item
          name="config"
          rules={[
            {
              required: true,
              message: 'Database connection is required.',
            },
          ]}
        >
          <DocumentConfig disabled={action === 'edit'} />
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
