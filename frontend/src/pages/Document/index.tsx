import Layout from '@/components/Layout';
import { PlusOutlined } from '@ant-design/icons';
import { Link, Outlet, useModel } from '@umijs/max';
import { Button } from 'antd';
import _ from 'lodash';
import NewCollection from './new';
import Sidebar from './sidebar';

export default () => {
  const { collections } = useModel('collection');
  const data = collections?.filter((c) => c.type === 'document');

  if (_.isEmpty(data)) {
    return <NewCollection />;
  }

  return (
    <Layout
      sidebar={{
        title: 'DocChat',
        content: <Sidebar />,
        extra: (
          <Link to="/document/new">
            <Button type="primary" icon={<PlusOutlined />}></Button>
          </Link>
        ),
      }}
    >
      <Outlet />
    </Layout>
  );
};
