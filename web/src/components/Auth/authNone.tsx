import type { User } from '@auth0/auth0-react';
import { useModel } from '@umijs/max';
import base64 from 'base-64';
import { useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';
import PageLoading from '../PageLoading';

export default (props: { children: React.ReactNode }): any => {
  const { user, setUser } = useModel('user');

  useEffect(() => {
    const _user: User = { email_verified: true };
    const localRaw = localStorage.getItem('u');
    if (localRaw) {
      try {
        _user.__raw = localRaw;
      } catch (err) {}
    }
    if (!_user.__raw) {
      const id = uuidv4();
      const idString = base64.encode(id);
      _user.__raw = idString;
      localStorage.setItem('u', idString);
    }
    _user.sub = base64.decode(_user.__raw);
    setUser(_user);
  }, []);

  if (!user) {
    return <PageLoading />;
  }

  return props.children;
};
