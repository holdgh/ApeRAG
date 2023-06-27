import { PageContainer } from '@ant-design/pro-components';
import { useModel } from '@umijs/max';
// import { useEffect } from 'react';

export default () => {
  const { currentCollection } = useModel('collection');

  return <PageContainer ghost></PageContainer>;
};
