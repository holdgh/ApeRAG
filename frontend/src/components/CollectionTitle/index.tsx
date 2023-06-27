import { Collection } from '@/models/collection';
import { DatabaseOutlined, SnippetsOutlined, VideoCameraOutlined } from '@ant-design/icons';
import { Space, Typography } from 'antd';

export default ({ collection }: { collection?: Collection }) => {
  return (
    <Typography.Title level={4}>
      <Space>
        {collection?.type === 'document' ? (
          <SnippetsOutlined style={{ fontSize: 18 }} />
        ) : null}
        {collection?.type === 'multimedia' ? (
          <VideoCameraOutlined style={{ fontSize: 18 }} />
        ) : null}
        {collection?.type === 'database' ? (
          <DatabaseOutlined style={{ fontSize: 18 }} />
        ) : null}
        {collection?.title}
      </Space>
    </Typography.Title>
  );
};
