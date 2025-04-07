import { env } from '@/models/system';
import { Auth0Provider } from '@auth0/auth0-react';
import { GuardProvider } from '@authing/guard-react18';
import { LogtoProvider, UserScope } from '@logto/react';
import { Outlet } from '@umijs/max';

import Auth0 from './auth0';
import Authing from './authing';
import AuthNone from './authNone';
import Logto from './logto';

export const AuthProvider = (props: { children: JSX.Element }) => {
  if (env?.auth?.type === 'authing') {
    return (
      <GuardProvider
        appId={env.auth.auth_app_id}
        redirectUri={window.location.origin + `${BASE_PATH}/callback`}
      >
        {props.children}
      </GuardProvider>
    );
  }

  if (env?.auth?.type === 'auth0') {
    return (
      <Auth0Provider
        domain={env.auth.auth_domain}
        clientId={env.auth.auth_app_id}
        authorizationParams={{
          redirect_uri: window.location.origin + BASE_PATH + '/callback',
        }}
      >
        {props.children}
      </Auth0Provider>
    );
  }

  if (env?.auth?.type === 'logto') {
    return (
      <LogtoProvider
        config={{
          endpoint: env.auth.auth_domain,
          appId: env.auth.auth_app_id,
          scopes: [
            UserScope.Email,
            UserScope.Profile,
            UserScope.Phone,
            UserScope.CustomData,
            UserScope.Identities,
          ],
        }}
      >
        {props.children}
      </LogtoProvider>
    );
  }

  if (env?.auth?.type === 'none') {
    return props.children;
  }
};

export default (props: { children: JSX.Element }): any => {
  if (env?.auth?.type === 'auth0') {
    return <Auth0>{props.children || <Outlet />}</Auth0>;
  }

  if (env?.auth?.type === 'logto') {
    return (
      <Logto>{props.children || <Outlet />}</Logto>
    );
  }

  if (env?.auth?.type === 'none') {
    return <AuthNone>{props.children || <Outlet />}</AuthNone>;
  }

  if (env?.auth?.type === 'authing') {
    return <Authing>{props.children || <Outlet />}</Authing>;
  }
};
