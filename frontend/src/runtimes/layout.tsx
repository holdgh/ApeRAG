import { getUser } from '@/models/user';
import auth0 from '@/utils/auth0';
import {
  LoginOutlined,
  LogoutOutlined,
  SettingFilled,
} from '@ant-design/icons';
import { Link } from '@umijs/max';
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
      sider: {
        colorMenuBackground: '#35363A',
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
        <Link key="settings" to="/settings">
          <Typography.Text type="secondary" style={actionTextStyle}>
            <SettingFilled />
          </Typography.Text>
        </Link>,
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
