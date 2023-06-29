import CheckedCard from '@/components/CheckedCard';
import { DatabaseOutlined, SnippetsOutlined } from '@ant-design/icons';
import { Button, Form, FormInstance, Input } from 'antd';

type Props = {
  type: "add" | "edit";
  onFinish: () => void;
  form: FormInstance;
};

export default ({ onFinish, form, type }: Props) => {
  return (
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
          disabled={type === 'edit'}
          options={[
            {
              icon: <SnippetsOutlined />,
              label: 'Document',
              value: 'document',
              description: 'Use docx, pptx, csv, pdf, or md as a collection.',
            },
            {
              icon: <DatabaseOutlined />,
              label: 'Database',
              value: 'database',
              description: 'Use database as a collection.',
            },
          ]}
        />
      </Form.Item>

      <Form.Item>
        <Button type="primary" htmlType="submit">
          { type === "add" ? "Create" : "Update" }
        </Button>
      </Form.Item>
    </Form>
  );
};
