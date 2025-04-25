import { LOCALES, TOPBAR_HEIGHT } from '@/constants';
import { api } from '@/services';
import {
  CheckOutlined,
  GithubOutlined,
  LoginOutlined,
  MoonOutlined,
  SunOutlined,
  UserOutlined,
} from '@ant-design/icons';
import {
  Avatar,
  Button,
  ButtonProps,
  Card,
  Divider,
  Dropdown,
  GlobalToken,
  Image,
  Menu,
  MenuProps,
  Space,
  theme,
  Typography,
} from 'antd';
import alpha from 'color-alpha';
import { useAuth } from 'oidc-react';
import { useMemo } from 'react';
import {
  createGlobalStyle,
  css,
  getLocale,
  Link,
  setLocale,
  styled,
  useIntl,
  useLocation,
  useModel,
} from 'umi';
import styles from './topbar.less';

export const GlobalStyles = createGlobalStyle<{
  token: GlobalToken;
}>`
  ${({ token }) => {
    return `
      body {
        background: ${token.colorBgLayout};
        --toastify-font-family: ${token.fontFamily};
        --toastify-color-light: ${token.colorBgContainer};
        --toastify-color-dark: ${token.colorBgContainer};
        --toastify-color-info: ${token.colorInfo};
        --toastify-color-success: ${token.colorSuccess};
        --toastify-color-warning: ${token.colorWarning};
        --toastify-color-error: ${token.colorError};
        --toastify-toast-shadow: ${token.boxShadow};
        --toastify-toast-offset: 24px;
      }
    `;
  }}
`;

const StyledTopbar = styled('header').withConfig({
  shouldForwardProp: (prop) => !['token'].includes(prop),
})<{
  token: GlobalToken;
}>`
  ${({ token }) => css`
    padding-inline: ${token.padding}px;
    height: ${TOPBAR_HEIGHT}px;
    border-bottom: 1px solid ${token.colorBorderSecondary};
    display: flex;
    justify-content: space-between;
    backdrop-filter: blur(20px);
    background-color: ${alpha(token.colorBgLayout, 0.75)};
    z-index: ${token.zIndexPopupBase};
    position: fixed;
    left: 0;
    right: 0;
    top: 0;
    box-shadow: ${token.boxShadowTertiary};
    // background: ${token.colorBgContainer};
  `}
`;

export default () => {
  const { token } = theme.useToken();
  const { themeName, setThemeName } = useModel('global');
  const { user } = useModel('user');
  const locale = getLocale();
  const location = useLocation();
  const { formatMessage } = useIntl();

  const { type } = APERAG_CONFIG.auth || {};
  const oidc =
    type && ['auth0', 'authing', 'logto'].includes(type)
      ? useAuth()
      : undefined;

  const login = async () => {};
  const logout = async () => {
    if (oidc) {
      await oidc?.signOut();
      window.location.reload();
    }
    if (type === 'cookie') {
      const res = await api.logoutPost();
      if (res.status === 200) window.location.reload();
    }
  };

  const menuItems: MenuProps['items'] = useMemo(() => {
    let data: MenuProps['items'] = [
      ...LOCALES.map(({ label, key }) => ({
        key,
        label,
        icon: (
          <CheckOutlined
            style={{ visibility: locale === key ? 'visible' : 'hidden' }}
          />
        ),
        onClick: () => setLocale(key),
      })),
      { type: 'divider' },
    ];
    data = data.concat({
      key: 'logtout',
      label: user
        ? formatMessage({ id: 'action.signout' })
        : formatMessage({ id: 'action.signin' }),
      icon: <LoginOutlined />,
      onClick: user ? logout : login,
    });
    return data;
  }, [user]);

  const rightButtonItemProps: ButtonProps = {
    type: 'text',
    shape: 'circle',
  };

  const getLogoSrc = () => {
    const defaultImgSrc = `${PUBLIC_PATH}logo_${themeName}.png`;
    switch (themeName) {
      case 'light':
        return APERAG_CONFIG.logo_light
          ? APERAG_CONFIG.logo_light
          : defaultImgSrc;
      case 'dark':
        return APERAG_CONFIG.logo_dark
          ? APERAG_CONFIG.logo_dark
          : defaultImgSrc;
    }
  };

  return (
    <>
      <GlobalStyles token={token} />
      <StyledTopbar token={token}>
        <Link to="/" className={styles.logo}>
          <Space>
            <Image className={styles.img} src={getLogoSrc()} preview={false} />
            <Typography.Text className={styles.text}>
              {APERAG_CONFIG.title}
            </Typography.Text>
          </Space>
        </Link>
        <Space className={styles.topnav}></Space>
        <Space>
          {APERAG_CONFIG.github && (
            <a href={APERAG_CONFIG.github} target="_blank" rel="noreferrer">
              <Button {...rightButtonItemProps} icon={<GithubOutlined />} />
            </a>
          )}
          <Button
            disabled={location.pathname === '/'}
            onClick={() => {
              setThemeName(themeName === 'dark' ? 'light' : 'dark');
            }}
            {...rightButtonItemProps}
            icon={themeName === 'dark' ? <SunOutlined /> : <MoonOutlined />}
          />
          <Dropdown
            dropdownRender={() => {
              return (
                <Card
                  styles={{ body: { padding: 4 } }}
                  className={styles.userContainer}
                >
                  {user && (
                    <>
                      <Space className={styles.info}>
                        <Avatar
                          size="large"
                          icon={<UserOutlined style={{ fontSize: 14 }} />}
                        />
                        <div>
                          <Typography.Text>{user?.username}</Typography.Text>
                          {user?.email && (
                            <Typography.Text className={styles.email}>
                              {user.email}
                            </Typography.Text>
                          )}
                        </div>
                      </Space>
                      <Divider style={{ marginBlock: 4 }} />
                    </>
                  )}
                  <Menu className={styles.menu} items={menuItems} />
                </Card>
              );
            }}
          >
            <Avatar
              style={{ cursor: 'pointer' }}
              icon={<UserOutlined style={{ fontSize: 14 }} />}
            />
          </Dropdown>
        </Space>
      </StyledTopbar>
    </>
  );
};
