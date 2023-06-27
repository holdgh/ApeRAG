import { getUser } from '@/models/user';
import auth0 from '@/utils/auth0';
import {
  FileTextOutlined,
  PlusOutlined,
  UserOutlined,
} from '@ant-design/icons';
import { Link, Outlet, useModel } from '@umijs/max';
import { Button, Card, CardProps, Result } from 'antd';
import { useEffect } from 'react';

export default (): React.ReactNode => {
  const { collections, getCollections } = useModel('collection');
  const user = getUser();

  useEffect(() => {
    if (user) getCollections();
  }, [user]);

  const cardProps: CardProps = {
    bordered: false,
    bodyStyle: { padding: '100px 0', textAlign: 'center' },
    style: { marginTop: 120 },
  };

  if (!user) {
    return (
      <Card {...cardProps}>
        <Result
          icon={<UserOutlined />}
          title="Before accessing the system, you need to register an account and log in."
          subTitle="Click the button below to login."
          extra={[
            <Button
              size="large"
              type="primary"
              key="login"
              onClick={() => {
                auth0.loginWithRedirect();
              }}
            >
              Login
            </Button>,
          ]}
        />
      </Card>
    );
  }

  if (!user.email_verified) {
    return (
      <Card {...cardProps}>
        <Result
          icon={<UserOutlined />}
          title="We have just sent an email to your mailbox, please confirm the verification identity"
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
              Reload
            </Button>,
          ]}
        />
      </Card>
    );
  }

  if (collections && !collections.length) {
    return (
      <Card {...cardProps}>
        <Result
          icon={<FileTextOutlined />}
          title="KubeChat is a new chatbot based on local datasets and utilizes multiple large language models."
          subTitle="Click the button below to get started."
          extra={[
            <Link to="/collections/new" key="createCollection">
              <Button type="primary" icon={<PlusOutlined />}>
                Create a collection
              </Button>
            </Link>,
          ]}
        />
      </Card>
    );
  }

  return <Outlet />;

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
};
