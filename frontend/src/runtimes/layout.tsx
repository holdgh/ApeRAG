import ChildrenRender from '@/components/ChildrenRender';
import { getUser } from '@/models/user';
import auth0 from '@/utils/auth0';
import {
  LoginOutlined,
  LogoutOutlined,
  PlusOutlined,
  SettingFilled,
} from '@ant-design/icons';
import { Link } from '@umijs/max';
import { Button, Typography } from 'antd';
import type { InitialStateType } from './getInitialState';

let hasInit = localStorage.getItem('sidebarCollapsed') !== 'true';
export const layout = ({
  initialState,
  setInitialState,
}: {
  initialState: InitialStateType;
  setInitialState: any;
}) => {
  const logo = 'https://opendbms.com/client/favicon.ico';
  const title = 'KubeChat';
  const user = getUser();
  return {
    logo,
    title,
    menu: {
      locale: false,
    },
    contentWidth: 'Fixed', //'Fluid',
    disableMobile: false,
    collapsed: initialState?.collapsed,
    onCollapse: (collapsed: boolean) => {
      if (!hasInit) {
        hasInit = true;
        return;
      }
      localStorage.setItem('sidebarCollapsed', String(collapsed));
      setInitialState((s: InitialStateType) => ({ ...s, collapsed }));
      hasInit = true;
    },
    // disableMobile: true,
    // collapsed: true,
    collapsedButtonRender: () => null,
    token: {
      bgLayout: '#0A0A0A',
      sider: {
        colorMenuBackground: '#202027',
      },
      header: {},
      pageContainer: {
        // paddingBlockPageContainerContent: 0,
        // paddingInlinePageContainerContent: 0,
      },
    },
    menuFooterRender: () => {
      if (initialState?.collapsed) return;
      return (
        <div
          style={{
            fontSize: 12,
            textAlign: 'center',
            color: 'rgba(255, 255, 255, 0.15)',
          }}
        >
          © 2023 ApeCloud PTE. Ltd.
        </div>
      );
    },
    menuExtraRender: () => {
      return (
        <Link to="/collections/new">
          <Button block type="primary" icon={<PlusOutlined />}>
            {initialState?.collapsed ? '' : 'Create a collection'}
          </Button>
        </Link>
      );
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
    childrenRender: ChildrenRender,
  };
};
