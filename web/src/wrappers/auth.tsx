import PageLoading from '@/components/PageLoading';
import auth0Client from '@/utils/auth0';
import authingClient from '@/utils/authing';
import { getUniqColor } from '@/utils/color';
import feishu from '@/utils/feishu';
import { User } from '@auth0/auth0-spa-js';
import { Outlet, useModel } from '@umijs/max';
import base64 from 'base-64';
import { useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';

export default () => {
  const { bots } = useModel('bot');
  const { user, setUser } = useModel('user');

  const authingLogin = async () => {
    if (!authingClient) return;

    try {
      const _user = await authingClient.trackSession();
      const isExpired =
        new Date().getTime() > new Date(_user?.tokenExpiredAt).getTime();

      if (!_user || isExpired) {
        console.log('start login....');
        authingClient.startWithRedirect({
          scope: 'openid email',
          state: window.location.href,
        });
        return;
      }
      const user = {
        __raw: _user.token,
        email_verified: _user.emailVerified || false,
        email: _user.email || '',
        picture: `https://ui-avatars.com/api/?background=${getUniqColor(
          _user?.email,
        ).replace('#', '')}&color=fff&name=${_user?.email}`,
      };
      setUser(user);
    } catch (err: any) {
      console.error(err);
    }
  };

  const auth0Login = async () => {
    if (!auth0Client) return;

    try {
      await auth0Client.getTokenSilently();
    } catch (err: any) {}

    const _user = await auth0Client.getIdTokenClaims();
    if (!_user) {
      await auth0Client.loginWithRedirect({
        appState: {
          targetUrl: window.location.href,
        },
      });
    } else {
      setUser(_user);
    }
  };

  const feishuLogin = async () => {
    await feishu.loginWithRedirect();
  };

  const anonymousLogin = async () => {
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
  };

  useEffect(() => {
    switch (AUTH_TYPE) {
      case 'none':
        anonymousLogin();
        break;
      case 'auth0':
        auth0Login();
        break;
      case 'authing':
        authingLogin();
        break;
      case 'feishu':
        feishuLogin();
        break;
    }
  }, []);

  if (user) {
    return bots === undefined ? null : <Outlet />;
  } else {
    return <PageLoading mask={true} />;
  }
};
