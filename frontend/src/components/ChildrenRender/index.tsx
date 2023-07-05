import { getUser } from '@/models/user';
import { PlusOutlined, WechatFilled } from '@ant-design/icons';
import { Link, Outlet, history, useModel } from '@umijs/max';
import { Button, Result, Typography } from 'antd';
import { useEffect } from 'react';
import { CSSTransition, TransitionGroup } from 'react-transition-group';
import PageLoading from '../PageLoading';
import './index.less';

export default (): React.ReactNode => {
  const { collections, getCollections, collectionLoading } =
    useModel('collection');
  const user = getUser();

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

  const style = {
    marginTop: 100,
  };

  const TipIcon = (
    <Typography.Text>
      <WechatFilled style={{ opacity: 0.05, fontSize: 200 }} />
    </Typography.Text>
  );

  if (!user.email_verified) {
    return (
      <Result
        style={style}
        icon={TipIcon}
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
    return <Result style={style} icon={TipIcon} />;
  }

  if (collections?.length === 0 && !ignore) {
    return (
      <Result
        style={style}
        icon={TipIcon}
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
    );
  }

  if (history.location.pathname.match(/^\/chat/)) return <Outlet />;

  return (
    <div style={{ position: 'relative' }}>
      <TransitionGroup component={null}>
        <CSSTransition
          key={history.location.pathname}
          classNames="fade"
          timeout={600}
        >
          <div style={{ position: 'absolute', left: 0, right: 0 }}>
            <Outlet />
          </div>
        </CSSTransition>
      </TransitionGroup>
    </div>
  );
};
