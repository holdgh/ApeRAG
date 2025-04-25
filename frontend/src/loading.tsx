import { useEffect } from 'react';
import { useModel } from 'umi';

export default () => {
  const { setLoading } = useModel('global');

  useEffect(() => {
    setLoading(true);
    return () => setLoading(false);
  }, []);

  return <></>;
};
