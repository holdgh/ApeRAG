import { Outlet, useModel } from 'umi';

export const LayoutBot = () => {
  const { bot } = useModel('bot');
  if (!bot) return;
  return <Outlet />;
};
