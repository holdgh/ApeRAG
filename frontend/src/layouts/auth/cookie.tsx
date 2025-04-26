import { useEffect } from 'react';
import { useModel } from 'umi';
import Loading from './loading';

export default ({ children }: { children: React.ReactNode }) => {
  const { user, getUser } = useModel('user');

  useEffect(() => {
    getUser();
  }, []);

  if (!user) {
    return <Loading />;
  }

  return children;
};
