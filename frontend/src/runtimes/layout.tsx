import { getUser } from '@/models/user';
import auth0 from '@/utils/auth0';
import { LoginOutlined, LogoutOutlined } from '@ant-design/icons';
import { Typography } from 'antd';

export const layout = () => {
  const logo = 'https://opendbms.com/client/favicon.ico';
  const title = 'KubeChat';
  const user = getUser();
  return {
    logo,
    title,
    menu: {
      locale: false,
    },
    contentWidth: 'Fixed', // Fixed | Fluid
    disableMobile: true,
    collapsed: true,
    collapsedButtonRender: () => null,
    token: {
      bgLayout: '#0A0A0A',
      sider: {
        colorMenuBackground: '#35363A',
        colorBgMenuItemSelected: 'rgba(255, 255, 255, 0.1)',
      },
      header: {},
      pageContainer: {},
    },
    avatarProps: {
      src: user?.picture,
      title: user?.nickname || 'unkown',
    },
    actionsRender: (props: any) => {
      if (props.isMobile) return [];
      const actionTextStyle = {
        paddingInline: 8,
      };
      return [
        user ? (
          <Typography.Text type="secondary" style={actionTextStyle}>
            <LoginOutlined
              key="logout"
              onClick={() => {
                auth0.logout();
              }}
            />
          </Typography.Text>
        ) : (
          <Typography.Text type="secondary" style={actionTextStyle}>
            <LogoutOutlined
              key="login"
              onClick={() => {
                auth0.loginWithRedirect();
              }}
            />
          </Typography.Text>
        ),
      ];
    },
  };
};
