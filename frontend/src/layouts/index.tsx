import PageLoading from '@/components/PageLoading';
import { getUser } from '@/models/user';
import { WechatFilled } from '@ant-design/icons';
import { Outlet, useModel } from '@umijs/max';
import { Button, Result, Typography } from 'antd';
import { useEffect } from 'react';

export default () => {
  const { collections, getCollections } = useModel('collection');
  const user = getUser();

  useEffect(() => {
    if (user) getCollections();
  }, []);

  if (!user) {
    return <PageLoading mask={true} />;
  }

  if (!user.email_verified) {
    return (
      <Result
        style={{
          marginTop: 100,
        }}
        icon={
          <Typography.Text>
            <WechatFilled style={{ opacity: 0.05, fontSize: 200 }} />
          </Typography.Text>
        }
        title={
          <Typography.Text style={{ fontSize: 18 }}>
            We have just sent an email to your mailbox, confirm the verification
            identity.
          </Typography.Text>
        }
        subTitle="Click the button below to check again."
        extra={[
          <Button
            size="large"
            type="primary"
            key="reload"
            onClick={() => {
              window.location.reload();
            }}
          >
            Refresh
          </Button>,
        ]}
      />
    );
  }

  if (collections === undefined) {
    return null;
  }

  return <Outlet />;
};
