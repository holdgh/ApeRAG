import PageLoading from '@/components/PageLoading';
import { useAuth0 } from '@auth0/auth0-react';
import { useModel } from '@umijs/max';
import { useEffect } from 'react';
import EmailConfirm from './emailConfirm';

export default (props: { children: React.ReactNode }): any => {
  const { user, setUser } = useModel('user');
  const { loginWithRedirect, isLoading, getIdTokenClaims } = useAuth0();

  const login = async () => {
    if (user || isLoading) return;
    
    const _user = await getIdTokenClaims();
    if (_user) {
      setUser(_user);
    } else {
      await loginWithRedirect({
        appState: {
          targetUrl: window.location.href,
        },
      });
    }
  };

  useEffect(() => {
    if (!isLoading) login();
  }, [isLoading]);

  if (!user) {
    return <PageLoading />;
  }

  if (!user.email_verified) {
    return <EmailConfirm />;
  }

  return props.children;
};
