import { history, useSearchParams } from '@umijs/max';
import { useEffect } from 'react';

import { env } from '@/models/system';
import { useGuard } from '@authing/guard-react18';
import { useHandleSignInCallback } from '@logto/react';

export default (): any => {
  const [searchParams] = useSearchParams();
  const authingClient = useGuard();
  const code = searchParams.get('code');
  
  if (env.auth.type === 'logto') {
    useHandleSignInCallback(() => {
      history.replace('/bots');
    });
  }

  const handleAuthingCallback = async () => {
    try {
      await authingClient.handleRedirectCallback();
      const loginStatus = await authingClient.checkLoginStatus();
      if (!loginStatus) {
        authingClient.logout();
        return;
      }
      const state = searchParams.get('state');
      if (state) {
        window.location.href = state.match(/\/callback/) ? BASE_PATH : state;
      } else {
        window.location.href = BASE_PATH;
      }
    } catch (e) {
      authingClient.startWithRedirect({
        scope: 'openid email',
        state: window.location.href,
      });
      console.error('Guard handleAuthingLoginCallback error: ', e);
    }
  };

  const handleAuth0Callback = async () => {
    history.replace('/bots');
  };

  const handleLogtoCallback = async () => {
    
  };

  useEffect(() => {
    if (env.auth.type === 'authing') {
      handleAuthingCallback();
    }
    if (env.auth.type === 'auth0') {
      handleAuth0Callback();
    }
    if (env.auth.type === 'logto') {
      handleLogtoCallback();
    }
  }, [code]);

  return null;
};
