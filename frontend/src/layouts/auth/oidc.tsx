import { Result, theme } from 'antd';
import { useAuth } from 'oidc-react';
import { useEffect } from 'react';
import { UndrawWorkChat } from 'react-undraw-illustrations';
import { FormattedMessage, useModel } from 'umi';
import Loading from './loading';

export default ({ children }: { children: React.ReactNode }): any => {
  const { oidcUser, setOidcUser, user } = useModel('user');
  const { userData, signIn, isLoading } = useAuth();
  const { token } = theme.useToken();

  useEffect(() => {
    if (isLoading) return;

    if (userData) {
      setOidcUser(userData);
    } else {
      signIn({
        redirect_uri: `${window.location.origin}${BASE_PATH}callback?redirectUri=${encodeURIComponent(window.location.href)}`,
      });
    }
  }, [isLoading, userData]);

  if (oidcUser && oidcUser.profile.email && !oidcUser.profile.email_verified) {
    return (
      <Result
        icon={
          <UndrawWorkChat primaryColor={token.colorPrimary} height="200px" />
        }
        title={<FormattedMessage id="text.welcome" />}
        subTitle={<FormattedMessage id="text.emailConfirm" />}
      />
    );
  }

  if (!user) {
    return <Loading />;
  }

  return children;
};
