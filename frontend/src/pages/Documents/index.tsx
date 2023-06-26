import { MessageOutlined } from '@ant-design/icons';
import { PageContainer } from '@ant-design/pro-components';
import { Link, Outlet, history, useParams } from '@umijs/max';
import { Button } from 'antd';
import { useEffect, useState } from 'react';

export default () => {
  const { collectionId } = useParams();

  const key = history.location.pathname.replace(/.*\//, '');

  const [tabActiveKey, setTabActiveKey] = useState<string>(key);

  useEffect(() => {
    setTabActiveKey(key);
  }, [key]);

  return (
    <PageContainer
      ghost
      extra={[
        <Link to="/chat" key="1">
          <Button type="primary" icon={<MessageOutlined />}>
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
