import { FileTextOutlined, PlusOutlined } from '@ant-design/icons';
import { Link } from '@umijs/max';
import { Button, Card, Space, Typography } from 'antd';
import React from 'react';

interface Props {}

const NoCollections: React.FC<Props> = (props: Props) => {
  return (
    <Card
        bordered={false}
        bodyStyle={{ padding: '100px 0', textAlign: 'center'}}
        style={{marginTop: 120 }}
      >
      <Space size="large" direction="vertical">
        <FileTextOutlined style={{ fontSize: 50 }} />
        <div>
          <Typography.Paragraph>
            KubeChat is a new chatbot based on local datasets and utilizes
            multiple large language models.
          </Typography.Paragraph>
          <Typography.Paragraph>
            Click the button below to get started.
          </Typography.Paragraph>
        </div>
        <Link to="/collections/new">
          <Button type="primary" icon={<PlusOutlined />}>
            Create a collection
          </Button>
        </Link>
      </Space>
    </Card>
  );
};

export default NoCollections;
