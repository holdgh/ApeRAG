import ChildrenRender from '@/components/ChildrenRender';
import auth0 from '@/utils/auth0';
import { LoginOutlined, LogoutOutlined, PlusOutlined } from '@ant-design/icons';
import { Link } from '@umijs/max';
import { Button, Tooltip } from 'antd';
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
  return {
    logo,
    title,
    menu: {
      locale: false,
    },
    disableMobile: true,
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
    token: {
      bgLayout: '#0A0A0A',
      sider: {
        colorMenuBackground: '#202027',
        colorBgMenuItemSelected: '#0A0A0A',
      },
      pageContainer: {},
    },
    menuFooterRender: () => {
      if (initialState?.collapsed) return;
      return (
        <div style={{ fontSize: 12, textAlign: 'center' }}>
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
      src: initialState?.user?.picture,
      title: initialState?.user?.nickname || 'unkown',
      size: 'small',
    },
    actionsRender: (props: any) => {
      if (props.isMobile) return [];
      return [
        initialState?.user ? (
          <Tooltip title="logout">
            <LoginOutlined
              key="logout"
              onClick={() => {
                auth0.logout();
              }}
            />
          </Tooltip>
        ) : (
          <Tooltip title="login">
            <LogoutOutlined
              key="login"
              onClick={() => {
                auth0.loginWithRedirect();
              }}
            />
          </Tooltip>
        ),
      ];
    },
    childrenRender: ChildrenRender,
    // menuHeaderRender: (logo) => {
    //   return (
    //     <Space style={{ justifyContent: "space-between", width: "100%" }}>
    //       <Space>
    //         { logo }
    //         { title }
    //       </Space>
    //       <Button type="primary" icon={<PlusOutlined />} />
    //     </Space>
    //   )
    // }
  };
};
