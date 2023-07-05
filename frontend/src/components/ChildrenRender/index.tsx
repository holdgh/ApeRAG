import { getUser } from '@/models/user';
import {
  FileTextOutlined,
  PlusOutlined,
  UserOutlined,
} from '@ant-design/icons';
import { Link, Outlet, history, useModel } from '@umijs/max';
import { Button, Card, CardProps, Result, Typography } from 'antd';
import { useEffect } from 'react';
import PageLoading from '../PageLoading';
import './index.less';

export default (): React.ReactNode => {
  const { collections, getCollections } = useModel('collection');
  const user = getUser();

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
    return <PageLoading mask={true} />;
  }

  if (!user.email_verified) {
    return (
      <Card {...cardProps}>
        <Result
          status={'error'}
          icon={<UserOutlined />}
          title={
            <Typography.Text style={{ fontSize: 18 }}>
              We have just sent an email to your mailbox, confirm the
              verification identity.
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
      </Card>
    );
  }

  if (collections === undefined) return null;

  if (collections.length === 0 && !ignore) {
    return (
      <Card {...cardProps}>
        <Result
          status={'info'}
          icon={<FileTextOutlined />}
          title={
            <Typography.Text style={{ fontSize: 18 }}>
              KubeChat is a new chatbot based on local datasets and utilizes
              multiple large language models.
            </Typography.Text>
          }
          subTitle="Click the button below to get started."
          extra={[
            <Link to="/collections/new" key="createCollection">
              <Button size="large" type="primary" icon={<PlusOutlined />}>
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
  //     <CSSTransition key={history.location.pathname} classNames="fade" timeout={600}>
  //       <Outlet />
  //     </CSSTransition>
  //   </TransitionGroup>
  // );
};
