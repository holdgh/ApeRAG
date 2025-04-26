import base64 from 'base-64';
import { User as OidcUser } from 'oidc-react';
import { useEffect } from 'react';
import { useModel } from 'umi';
import { v4 as uuidv4 } from 'uuid';
import Loading from './loading';

export default ({ children }: { children: React.ReactNode }): any => {
  const { setOidcUser, user } = useModel('user');

  useEffect(() => {
    let localToken = localStorage.getItem('u');
    if (!localToken) {
      const id = uuidv4();
      localToken = base64.encode(id);
      localStorage.setItem('u', localToken);
    }
    setOidcUser({
      id_token: localToken,
      profile: {},
    } as OidcUser);
  }, []);

  if (!user) {
    return <Loading />;
  }

  return children;
};
