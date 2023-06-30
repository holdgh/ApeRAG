import { Collection } from '@/models/collection';
import { AppstoreFilled, ReadFilled } from '@ant-design/icons';
import { Space, Typography } from 'antd';

export default ({ collection }: { collection?: Collection }) => {
  return (
    <Typography.Title level={4}>
      <Space>
        {collection?.type === 'document' ? (
          <ReadFilled style={{ fontSize: 16 }} />
        ) : null}
        {collection?.type === 'database' ? (
          <AppstoreFilled style={{ fontSize: 16 }} />
        ) : null}
        {collection?.title}
      </Space>
    </Typography.Title>
  );
};
