import { useLogto } from '@logto/react';
import { useModel } from '@umijs/max';
import { useEffect } from 'react';
import PageLoading from '@/components/PageLoading';
import EmailConfirm from './emailConfirm';

export default (props: { children: React.ReactNode }): any => {
  const { user, setUser } = useModel('user');
  const { signIn, getIdToken, fetchUserInfo } = useLogto();

  const login = async () => {
    if (user) return;

    const idToken = await getIdToken();
    const _user = await fetchUserInfo();

    if (_user) {
      setUser({
        __raw: idToken || '',
        email_verified: _user.email_verified || false,
        email: _user.email || '',
        username: _user.username || '',
        avatar: _user.picture,
      });
    } else {
      const redirect_uri = window.location.origin + BASE_PATH + '/callback';
      await signIn(redirect_uri);
    }
  };

  useEffect(() => {
    if(!user){
      login();
    }
  }, [user]);

  if (!user) {
    return <PageLoading />;
  }

  if (user.email && !user.email_verified) {
    return <EmailConfirm />;
  }

  return props.children;
};