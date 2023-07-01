import type { TypesCollection } from '@/models/collection';
import { AppstoreOutlined, ReadOutlined } from '@ant-design/icons';
import { Space, Typography } from 'antd';

export default ({ collection }: { collection?: TypesCollection }) => {
  return (
    <Typography.Title level={4} style={{ margin: 0 }}>
      <Space>
        {collection?.type === 'document' ? (
          <ReadOutlined style={{ fontSize: 16 }} />
        ) : null}
        {collection?.type === 'database' ? (
          <AppstoreOutlined style={{ fontSize: 16 }} />
        ) : null}
        {collection?.title}
      </Space>
    </Typography.Title>
  );
};
