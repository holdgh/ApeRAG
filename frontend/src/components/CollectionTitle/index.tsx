import { Collection } from '@/models/collection';
import { AppstoreOutlined, ReadOutlined } from '@ant-design/icons';
import { Space, Typography } from 'antd';

export default ({ collection }: { collection?: Collection }) => {
  return (
    <Typography.Title level={4}>
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
