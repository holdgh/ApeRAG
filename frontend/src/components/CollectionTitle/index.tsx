import { Collection } from '@/models/collection';
import {
  DatabaseOutlined,
  SnippetsOutlined,
} from '@ant-design/icons';
import { Space, Typography } from 'antd';

export default ({ collection }: { collection?: Collection }) => {
  return (
    <Typography.Title level={4}>
      <Space>
        {collection?.type === 'document' ? (
          <SnippetsOutlined style={{ fontSize: 16 }} />
        ) : null}
        {collection?.type === 'database' ? (
          <DatabaseOutlined style={{ fontSize: 16 }} />
        ) : null}
        {collection?.title}
      </Space>
    </Typography.Title>
  );
};
