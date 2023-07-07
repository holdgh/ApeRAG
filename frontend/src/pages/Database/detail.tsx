import { PageContainer } from '@ant-design/pro-components';
import { useModel, useParams } from '@umijs/max';
import { App, Button, Tabs, TabsProps, Typography } from 'antd';

import Edit from './edit';

export default () => {
  const { collectionId } = useParams();
  const { getCollection, deleteCollection } = useModel('collection');
  const { modal } = App.useApp();
  const collection = getCollection(collectionId);

  const onDelete = () => {
    if (!collectionId) return;

    modal.confirm({
      title: 'Comfirm',
      content: `delete ${collection?.title}?`,
      onOk: async () => {
        await deleteCollection(collection);
      },
    });
  };

  const items: TabsProps['items'] = [
    { label: 'Setting', key: 'setting', children: <Edit /> },
  ];

  return (
    <PageContainer
      ghost
      title={collection?.title}
      content={
        <Typography.Text type="secondary">
          {collection?.description}
        </Typography.Text>
      }
      extra={[
        <Button key={0} onClick={onDelete} danger>
          Delete
        </Button>,
      ]}
    >
      <Tabs defaultActiveKey="setting" items={items} />
    </PageContainer>
  );
};
