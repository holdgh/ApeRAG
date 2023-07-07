import { useModel } from '@umijs/max';

import SidebarItem from '@/components/SidebarItem';

export default () => {
  const { collections } = useModel('collection');
  const data = collections?.filter((c) => c.type === 'database');

  return (
    <>
      {data?.map((item, key) => {
        return <SidebarItem key={key} collection={item}></SidebarItem>;
      })}
    </>
  );
};
