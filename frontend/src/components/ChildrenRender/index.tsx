import auth0 from '@/utils/auth0';
import { UserOutlined } from '@ant-design/icons';
import { Outlet } from '@umijs/max';
import { Button, Card, Space, Typography } from 'antd';

import { getUser } from '@/models/user';

export default (): React.ReactNode => {
  const user = getUser();
  if (!user) {
    return (
      <Card
        bordered={false}
        bodyStyle={{ padding: '100px 0', textAlign: 'center' }}
        style={{ marginTop: 120 }}
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
        bordered={false}
        bodyStyle={{ padding: '100px 0', textAlign: 'center' }}
        style={{ marginTop: 120 }}
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

  // return (
  //   <TransitionGroup component={null}>
  //     <CSSTransition key={history.location.pathname} classNames="fade" timeout={5000}>
  //       <div style={{ position: 'relative' }}>
  //         <div style={{ position: 'absolute', width: '100%' }}>
  //           <Outlet />
  //         </div>
  //       </div>
  //     </CSSTransition>
  //   </TransitionGroup>
  // );
  return <Outlet />;
};
