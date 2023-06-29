import CollectionTitle from '@/components/CollectionTitle';
import { PageContainer } from '@ant-design/pro-components';
import { Outlet, history, useModel, useParams } from '@umijs/max';
import { Button, Typography } from 'antd';
import { useEffect, useState } from 'react';

export default () => {
  const { getCollection, setCurrentCollection } = useModel('collection');
  const { collectionId } = useParams();
  const key = history.location.pathname.replace(/.*\//, '');
  const [tabActiveKey, setTabActiveKey] = useState<string>(key);

  const collection = getCollection(collectionId);

  const tabList = [];
  if (collection?.type === 'document') {
    tabList.push({ tab: 'Documents', key: 'document' });
  }
  tabList.push({ tab: 'Setting', key: 'setting' });

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
        <Button
          key={1}
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
