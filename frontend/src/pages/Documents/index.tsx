import CollectionTitle from '@/components/CollectionTitle';
import { PageContainer } from '@ant-design/pro-components';
import { Outlet, history, useModel, useParams } from '@umijs/max';
import { App, Button, Typography } from 'antd';
import { useEffect, useState } from 'react';

export default () => {
  const { getCollection, deleteCollection, setCurrentCollection } =
    useModel('collection');
  const { collectionId } = useParams();
  const key = history.location.pathname.replace(/.*\//, '');
  const [tabActiveKey, setTabActiveKey] = useState<string>(key);
  const collection = getCollection(collectionId);
  const { modal } = App.useApp();

  const tabList = [];
  if (collection?.type === 'document') {
    tabList.push({ tab: 'Documents', key: 'document' });
  }
  tabList.push({ tab: 'Setting', key: 'setting' });

  const onDelete = () => {
    if (!collectionId) return;

    modal.confirm({
      title: 'Comfirm',
      content: `delete ${collection?.title}?`,
      onOk: async () => {
        await deleteCollection(collectionId);
      },
    });
  };

  useEffect(() => {
    setTabActiveKey(key);
  }, [key]);

  if (!collection) return;

  return (
    <PageContainer
      ghost
      title={<CollectionTitle collection={collection} />}
      content={
        <Typography.Text type="secondary">
          {collection?.description}
        </Typography.Text>
      }
      extra={[
        <Button key={0} onClick={onDelete} danger>
          Delete
        </Button>,
        <Button
          key={1}
          type="primary"
          onClick={async () => {
            await setCurrentCollection(collection);
            history.push('/chat');
          }}
        >
          Chat
        </Button>,
      ]}
      tabList={tabList}
      onTabChange={(key) => {
        history.push(`/collections/${collectionId}/${key}`);
      }}
      tabActiveKey={tabActiveKey}
    >
      <Outlet />
    </PageContainer>
  );
};
