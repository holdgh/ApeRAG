import { getUniqColor } from '@/utils/color';
import { useGuard } from '@authing/guard-react18';
import { useModel } from '@umijs/max';
import { useEffect } from 'react';
import PageLoading from '../PageLoading';
import EmailConfirm from './emailConfirm';

export default (props: { children: React.ReactNode }): any => {
  const { user, setUser } = useModel('user');
  const authingClient = useGuard();

  const login = async () => {
    if (!authingClient || user) return;
    let authing_local_user;
    try {
      authing_local_user = JSON.parse(
        localStorage.getItem('_authing_user') || '',
      );
    } catch (err) {}

    const isExpired =
      authing_local_user &&
      new Date().getTime() >
        new Date(authing_local_user.tokenExpiredAt).getTime();
    if (isExpired) {
      localStorage.removeItem('_authing_token');
      localStorage.removeItem('_authing_user');
      authingClient.logout({
        redirectUri: window.location.origin,
      });
      return;
    }

    const _idpUser = await authingClient.trackSession();
    if (_idpUser) {
      setUser({
        __raw: _idpUser.token,
        email_verified: _idpUser.emailVerified || false,
        email: _idpUser.email || '',
        avatar: `https://ui-avatars.com/api/?background=${getUniqColor(
          _idpUser?.email,
        ).replace('#', '')}&color=fff&name=${_idpUser?.email}`,
      });
    } else {
      authingClient.startWithRedirect({
        scope: 'openid email',
        state: window.location.href,
      });
      return;
    }
  };

  useEffect(() => {
    login();
  }, []);

  if (!user) {
    return <PageLoading />;
  }

  if (!user.email_verified) {
    return <EmailConfirm />;
  }

  return props.children;
};
