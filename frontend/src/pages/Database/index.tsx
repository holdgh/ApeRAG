import Layout from '@/components/Layout';
import SidebarItem from '@/components/SidebarItem';
import { PlusOutlined } from '@ant-design/icons';
import { Link, Outlet, useModel } from '@umijs/max';
import { Button } from 'antd';
import _ from 'lodash';
import NewCollection from './new';

export default () => {
  const { collections } = useModel('collection');
  const data = collections?.filter((c) => c.type === 'database');

  if (_.isEmpty(data)) {
    return <NewCollection />;
  }

  return (
    <Layout
      sidebar={{
        title: 'SQLChat',
        content: data?.map((item, key) => {
          return <SidebarItem key={key} collection={item}></SidebarItem>;
        }),
        extra: (
          <Link to="/database/new">
            <Button type="primary" icon={<PlusOutlined />}></Button>
          </Link>
        ),
      }}
    >
      <Outlet />
    </Layout>
  );
};
