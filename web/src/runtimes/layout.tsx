import { env } from '@/models/system';
import themeVariable from '@/variable';
import {
  CheckOutlined,
  LoginOutlined,
  LogoutOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import { useAuth0 } from '@auth0/auth0-react';
import { useGuard } from '@authing/guard-react18';
import { getLocale, setLocale, useModel } from '@umijs/max';
import { Dropdown, MenuProps, Space } from 'antd';

type LangInterface = {
  key: string;
  label: string;
  icon: string;
  title: string;
};
const defaultLangMap: LangInterface[] = [
  {
    key: 'en-US',
    label: 'English',
    icon: '🇺🇸',
    title: 'Language',
  },
  {
    key: 'zh-CN',
    label: '简体中文',
    icon: '🇨🇳',
    title: '语言',
  },
];

export const layout = () => {
  // eslint-disable-next-line react-hooks/rules-of-hooks
  const { user } = useModel('user');
  // eslint-disable-next-line react-hooks/rules-of-hooks
  const authingClient = useGuard();
  // eslint-disable-next-line react-hooks/rules-of-hooks
  const auth0Client = useAuth0();

  const login = () => {
    switch (env.auth.type) {
      case 'auth0':
        auth0Client.loginWithRedirect();
        break;
      case 'authing':
        authingClient.startWithRedirect({
          scope: 'openid email',
          state: window.location.href,
        });
        break;
    }
  };

  const logout = () => {
    switch (env.auth.type) {
      case 'auth0':
        auth0Client.logout({
          logoutParams: {
            returnTo: window.location.origin + BASE_PATH,
          },
        });
        break;
      case 'authing':
        authingClient.logout({
          redirectUri: window.location.origin,
        });
        break;
    }
  };

  return {
    logo: SITE_LOGO,
    title: SITE_TITLE,
    menu: {
      locale: false,
    },
    contentWidth: 'Fluid', // Fixed | Fluid
    disableMobile: true,
    collapsed: false,
    collapsedButtonRender: () => null,
    token: {
      bgLayout: themeVariable.backgroundColor,
      sider: {
        colorMenuBackground: themeVariable.sidebarBackgroundColor,
        colorBgMenuItemSelected: 'rgba(255, 255, 255, 0.06)',
      },
      header: {},
      pageContainer: {
        paddingBlockPageContainerContent: 80,
        paddingInlinePageContainerContent: 40,
      },
    },
    avatarProps: {
      src: user?.picture,
      title: user?.nickname || user?.email?.replace(/@.*/g, ''),
    },
    menuHeaderRender: () => {
      return (
        <Space>
          <img src={SITE_LOGO} width={26} height={26} />
          <h1 style={{ margin: 0 }}>{SITE_TITLE}</h1>
        </Space>
      );
    },
    actionsRender: (props: any) => {
      if (props.isMobile) return [];
      const locale = getLocale();
      const actions: MenuProps['items'] = [];
      defaultLangMap.forEach((item) => {
        actions.push({
          label: (
            <Space
              style={{
                marginLeft: 8,
                display: 'flex',
                justifyContent: 'space-between',
              }}
            >
              {item.label}
              <CheckOutlined
                style={{
                  visibility: locale === item.key ? 'visible' : 'hidden',
                }}
              />
            </Space>
          ),
          key: item.key,
          onClick: () => {
            setLocale(item.key, true);
          },
          icon: item.icon,
        });
      });

      if (env.auth.type === 'auth0' || env.auth.type === 'authing') {
        actions.push({ type: 'divider' });
        if (user) {
          actions.push({
            key: 'logout',
            label: 'Logout',
            onClick: logout,
            icon: <LoginOutlined />,
          });
        } else {
          actions.push({
            label: 'Login',
            key: 'login',
            onClick: login,
            icon: <LogoutOutlined />,
          });
        }
      }

      return [
        <Dropdown key="0" menu={{ items: actions }} trigger={['click']}>
          <SettingOutlined />
        </Dropdown>,
      ];
    },
  };
};
