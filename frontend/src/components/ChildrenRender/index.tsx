import auth0 from '@/utils/auth0';
import { UserOutlined } from '@ant-design/icons';
import { Outlet, useModel } from '@umijs/max';
import { Button, Card, Space, Typography } from 'antd';

export default (): React.ReactNode => {
  const { initialState } = useModel('@@initialState');
  const user = initialState?.user;

  if (!user) {
    return (
      <Card
        bodyStyle={{ padding: '150px 0', textAlign: 'center' }}
        bordered={false}
      >
        <Space size="large" direction="vertical">
          <UserOutlined style={{ fontSize: 50 }} />
          <div>
            <Typography.Paragraph>
              Before accessing the system, you need to register an account and
              log in.
            </Typography.Paragraph>
            <Typography.Paragraph>
              Click the button below to login.
            </Typography.Paragraph>
          </div>
          <Button
            size="large"
            type="primary"
            onClick={() => {
              auth0.loginWithRedirect();
            }}
          >
            Login
          </Button>
        </Space>
      </Card>
    );
  }

  if (!user.email_verified) {
    return (
      <Card
        bodyStyle={{ padding: '150px 0', textAlign: 'center' }}
        bordered={false}
      >
        <Space size="large" direction="vertical">
          <UserOutlined style={{ fontSize: 50 }} />
          <div>
            <Typography.Paragraph>
              We have just sent an email to your mailbox, please confirm the
              verification identity
            </Typography.Paragraph>
            <Typography.Paragraph>
              Click the button below to check again.
            </Typography.Paragraph>
          </div>
          <Button
            size="large"
            type="primary"
            onClick={() => {
              window.location.reload();
            }}
          >
            Reload
          </Button>
        </Space>
      </Card>
    );
  }

  return <Outlet />;
};
