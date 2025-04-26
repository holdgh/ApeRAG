import { NAVIGATION_WIDTH, SIDEBAR_WIDTH, TOPBAR_HEIGHT } from '@/constants';
import { GlobalToken, theme } from 'antd';
import { createGlobalStyle, css, Outlet, styled } from 'umi';
import { Auth } from './auth';
import { Sidebar } from './sidebar';
import Topbar from './topbar';

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

const StyledNavbarContainer = styled('nav').withConfig({
  shouldForwardProp: (prop) => !['token', 'sidebar', 'topbar'].includes(prop),
})<{
  token: GlobalToken;
  sidebar: boolean;
  topbar: boolean;
}>`
  ${({ token, sidebar, topbar }) => {
    return css`
      width: ${NAVIGATION_WIDTH}px;
      left: ${sidebar ? SIDEBAR_WIDTH : 0}px;
      top: ${topbar ? TOPBAR_HEIGHT : 0}px;
      bottom: 0;
      overflow: auto;
      border-right: 1px solid ${token.colorBorderSecondary};
      position: fixed;
      display: flex;
      flex-direction: column;
    `;
  }}
`;

const StyledMainContainer = styled('main').withConfig({
  shouldForwardProp: (prop) => !['sidebar', 'navbar', 'topbar'].includes(prop),
})<{
  topbar: boolean;
  sidebar: boolean;
  navbar: boolean;
}>`
  ${({ sidebar, navbar, topbar }) => {
    let offsetLeft = 0;

    if (sidebar) offsetLeft += SIDEBAR_WIDTH;
    if (navbar) offsetLeft += NAVIGATION_WIDTH;

    return css`
      ${offsetLeft ? `padding-left: ${offsetLeft}px` : ''};
      padding-top: ${topbar ? TOPBAR_HEIGHT : 0}px;
      transition: all 0s;
    `;
  }}
`;

export default ({
  topbar = true,
  sidebar = true,
  navbar,
  outlet,
  auth = true,
}: {
  topbar?: boolean;
  sidebar?: boolean;
  navbar?: React.ReactNode;
  outlet?: React.ReactNode;
  auth?: boolean;
}) => {
  const { token } = theme.useToken();

  const element = (
    <>
      {sidebar && <Sidebar topbar={topbar} />}
      {navbar && (
        <StyledNavbarContainer token={token} topbar={topbar} sidebar={sidebar}>
          {navbar}
        </StyledNavbarContainer>
      )}
      <StyledMainContainer
        topbar={topbar}
        sidebar={sidebar}
        navbar={Boolean(navbar)}
      >
        {outlet ? outlet : <Outlet />}
      </StyledMainContainer>
    </>
  );

  return (
    <>
      <GlobalStyles token={token} />
      {topbar && <Topbar />}
      {auth ? <Auth>{element}</Auth> : element}
    </>
  );
};
