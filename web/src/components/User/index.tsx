import { env } from '@/models/system';
import { useAuth0 } from '@auth0/auth0-react';
import { useGuard } from '@authing/guard-react18';
import { useLogto } from '@logto/react';
import { getLocale, setLocale, useIntl, useModel, history } from '@umijs/max';
import Avatar from '../../assets/default-avatar.png';
import Auth from '../Auth';
import { useEffect } from 'react';

function User() {
  const locale = getLocale();
  const intl = useIntl();

  const loginText = intl.formatMessage({
    id: 'bots.login',
  });
  const logoutText = intl.formatMessage({
    id: 'bots.logout',
  });
  const settingsText = intl.formatMessage({
    id: 'text.dev',
  });

  setLocale(locale);
  const { user } = useModel('user');

  let authingClient = null, auth0Client = null, logtoClient = null;

  if(env.auth.type==='authing'){
    authingClient = useGuard();
  }
  if(env.auth.type==='auth0'){
    auth0Client = useAuth0();
  }
  if(env.auth.type==='logto'){
    logtoClient = useLogto();
  }

  const login = () => {
    switch (env.auth.type) {
      case 'auth0':
        auth0Client?.loginWithRedirect();
        break;
      case 'logto':
        logtoClient?.signIn(window.location.origin + BASE_PATH + '/callback');
        break;
      case 'authing':
        authingClient?.startWithRedirect({
          scope: 'openid email',
          state: window.location.href,
        });
        break;
    }
  };

  const logout = () => {
    switch (env.auth.type) {
      case 'auth0':
        auth0Client?.logout({
          logoutParams: {
            returnTo: window.location.origin + BASE_PATH,
          },
        });
        break;
      case 'logto':
        logtoClient?.signOut(window.location.origin + BASE_PATH);
        break;
      case 'authing':
        authingClient?.logout({
          redirectUri: window.location.origin + BASE_PATH,
        });
        break;
    }
  };

  const goSetting = () => {
    history.push('/settings');
  }

  let email = user?.email;
  let username = user?.username || user?.nickname || email || 'Guest';

  return (
    <div className="user">
      {/* 权限校验 */}
      <Auth children={[]} />
      <a onClick={(e) => e.preventDefault()}>
        <div className="avatar">
          <img
            src={user?.picture ? user?.picture : Avatar}
            onError={(e) => {
              e.target.src = Avatar;
            }}
            title={username}
          />
        </div>
        <div className="nick">
          <div>
            <strong title={username}>{username}</strong>
            {email && (
              <em title={email}>{email}</em>
            )}
          </div>
        </div>
        <div className="action">
            ›
        </div>
        <nav>
          <ul>
            <li onClick={() => setLocale('en-US')} className={locale==='en-US'?'selected':''}><label className='en'>English</label></li>
            <li onClick={() => setLocale('zh-CN')} className={locale==='zh-CN'?'selected':''}><label className='cn'>简体中文</label></li>
            {user ? (
              <>
              <li onClick={goSetting}><label className='settings'>{settingsText}</label></li>
              <li onClick={logout}><label className='logout'>{logoutText}</label></li>
              </>
            ) : (
              <li onClick={login}><label className='login'>{loginText}</label></li>
            )}
          </ul>
        </nav>
      </a>
    </div>
  );
}

export default User;
