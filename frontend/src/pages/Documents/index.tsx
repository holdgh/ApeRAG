import { Collection } from '@/models/collection';
import { ReadCollection } from '@/services/collections';
import { MessageOutlined, SnippetsOutlined, VideoCameraOutlined } from '@ant-design/icons';
import { PageContainer } from '@ant-design/pro-components';
import { Link, Outlet, history, useParams } from '@umijs/max';
import { Button, Space, Typography } from 'antd';
import { useEffect, useState } from 'react';

export default () => {
  const [collection, setCollection] = useState<Collection>();
  const { collectionId } = useParams();
  const key = history.location.pathname.replace(/.*\//, '');
  const [tabActiveKey, setTabActiveKey] = useState<string>(key);

  const getCollection = async () => {
    if (!collectionId) return;
    const { data } = await ReadCollection(collectionId);
    setCollection(data);
  };

  useEffect(() => {
    setTabActiveKey(key);
  }, [key]);

  useEffect(() => {
    getCollection();
  }, []);

  return (
    <PageContainer
      ghost
      title={<Space>
        {collection?.type === 'Document' ? (
          <SnippetsOutlined style={{ fontSize: 24 }} />
        ) : null}
        {collection?.type === 'Multimedia' ? (
          <VideoCameraOutlined style={{ fontSize: 24 }} />
        ) : null}
        {collection?.title}
      </Space>}
      content={<Typography.Text type="secondary">{collection?.description}</Typography.Text>}
      extra={[
        <Link to="/chat" key="1">
          <Button>
            Chat
          </Button>
        </Link>,
      ]}
      tabList={[
        {
          tab: 'Documents',
          key: 'documents',
        },
        {
          tab: 'Setting',
          key: 'setting',
        },
      ]}
      onTabChange={(key) => {
        history.push(`/collections/${collectionId}/${key}`);
      }}
      tabActiveKey={tabActiveKey}
    >
      <Outlet />
    </PageContainer>
  );
};
