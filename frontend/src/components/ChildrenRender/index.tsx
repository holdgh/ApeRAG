import { getUser } from '@/models/user';
import {
  FileTextOutlined,
  PlusOutlined,
  UserOutlined,
} from '@ant-design/icons';
import { Link, Outlet, history, useModel } from '@umijs/max';
import { Button, Card, CardProps, Result, theme } from 'antd';
import { useEffect } from 'react';
import PageLoading from '../PageLoading';

export default (): React.ReactNode => {
  const { collections, getCollections } = useModel('collection');
  const user = getUser();
  const { token } = theme.useToken();

  const cardProps: CardProps = {
    bordered: false,
    bodyStyle: { padding: '100px 0', textAlign: 'center' },
    style: { marginTop: 120 },
  };

  useEffect(() => {
    if (user) getCollections();
  }, []);

  const whitelist = ['/collections/new'];
  const ignore = new RegExp(`^(${whitelist.join('|')})`).test(
    history.location.pathname,
  );

  if (!user) {
    return (
      <div
        style={{
          position: 'fixed',
          left: 0,
          right: 0,
          top: 0,
          bottom: 0,
          background: token.colorBgBase,
          zIndex: 100,
        }}
      >
        <PageLoading message="login..." />
      </div>
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

  if (collections === undefined) return null;

  if (collections.length === 0 && !ignore) {
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
