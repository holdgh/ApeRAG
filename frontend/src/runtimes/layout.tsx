import ChildrenRender from '@/components/ChildrenRender';
import { getUser } from '@/models/user';
import auth0 from '@/utils/auth0';
import {
  LoginOutlined,
  LogoutOutlined,
  PlusOutlined,
  QuestionCircleOutlined,
} from '@ant-design/icons';
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
  const user = getUser();
  return {
    logo,
    title,
    menu: {
      locale: false,
    },
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
    token: {
      bgLayout: '#0A0A0A',
      sider: {
        colorMenuBackground: '#202027',
      },
      header: {},
      pageContainer: {},
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
      return [
        <Tooltip title="Documents" key="docs">
          <QuestionCircleOutlined style={{ color: '#FFF' }} />
        </Tooltip>,
        user ? (
          <Tooltip title="logout">
            <LoginOutlined
              key="logout"
              style={{ color: '#FFF' }}
              onClick={() => {
                auth0.logout();
              }}
            />
          </Tooltip>
        ) : (
          <Tooltip title="login">
            <LogoutOutlined
              key="login"
              style={{ color: '#FFF' }}
              onClick={() => {
                auth0.loginWithRedirect();
              }}
            />
          </Tooltip>
        ),
      ];
    },
    childrenRender: ChildrenRender,
  };
};
