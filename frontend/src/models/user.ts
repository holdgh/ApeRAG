import { User } from '@/api';
import { api } from '@/services';
import { User as OidcUser } from 'oidc-react';
import { useEffect, useState } from 'react';
import { useModel } from 'umi';

/**
 * current login user
 */

let id_token: string | undefined;

export const getAuthorizationHeader = () => {
  if (id_token)
    return {
      Authorization: `Bearer ${id_token}`,
    };
};

export default () => {
  const [user, setUser] = useState<User>();
  const [userLoading, setUserLoading] = useState<boolean>(false);
  const [oidcUser, setOidcUser] = useState<OidcUser>();
  const { setLoading } = useModel('global');

  const getUser = async () => {
    setUserLoading(true);
    const res = await api.userGet();
    setUser({
      username: oidcUser?.profile.nickname || oidcUser?.profile.name || 'Guest',
      email: oidcUser?.profile.email,
      ...res.data,
    });
    setUserLoading(false);
  };

  useEffect(() => {
    if (!oidcUser) return;
    id_token = oidcUser?.id_token;
    getUser();
  }, [oidcUser]);

  useEffect(() => setLoading(userLoading), [userLoading]);

  return {
    oidcUser,
    setOidcUser,

    getUser,
    user,
    userLoading,
  };
};
