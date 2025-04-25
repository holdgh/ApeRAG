import { NAVIGATION_WIDTH, SIDEBAR_WIDTH, TOPBAR_HEIGHT } from '@/constants';
import { ArrowLeftOutlined } from '@ant-design/icons';
import { useHover } from 'ahooks';
import { Button, GlobalToken, Space, theme, Typography } from 'antd';
import { useRef } from 'react';
import { css, Link, styled } from 'umi';

const StyledNavigation = styled('nav').withConfig({
  shouldForwardProp: (prop) => !['token', 'sidebar', 'navbar'].includes(prop),
})<{
  token: GlobalToken;
  sidebar: boolean;
}>`
  ${({ token, sidebar }) => {
    return css`
      width: ${NAVIGATION_WIDTH}px;
      left: ${sidebar ? SIDEBAR_WIDTH : 0}px;
      top: ${TOPBAR_HEIGHT}px;
      bottom: 0;
      overflow: auto;
      border-right: 1px solid ${token.colorBorderSecondary};
      position: fixed;
      display: flex;
      flex-direction: column;
    `;
  }}
`;

const StyledNavigationHeader = styled('div').withConfig({
  shouldForwardProp: (prop) => !['token'].includes(prop),
})<{
  token: GlobalToken;
}>`
  ${({ token }) => {
    return css`
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: ${token.paddingXS}px;
      min-height: 48px;
    `;
  }}
`;

const StyledNavigationBody = styled('div')`
  ${() => {
    return css`
      padding: 0;
      flex: auto;
      overflow: auto;
    `;
  }}
`;

export const Navbar = ({
  sidebar = true,
  children,
}: {
  sidebar?: boolean;
  children: React.ReactNode;
}) => {
  const { token } = theme.useToken();
  return (
    <StyledNavigation token={token} sidebar={sidebar}>
      {children}
    </StyledNavigation>
  );
};

export const NavbarHeader = ({
  title,
  backTo,
  children,
}: {
  title?: string;
  backTo?: string;
  children?: React.ReactNode;
}) => {
  const { token } = theme.useToken();

  const ref = useRef(null);
  const isHovering = useHover(ref);

  return (
    <StyledNavigationHeader ref={ref} token={token}>
      {backTo ? (
        <Link to={backTo}>
          <Space>
            <Button type="text" icon={<ArrowLeftOutlined />} />
            <Typography.Text ellipsis style={{ maxWidth: 130 }}>
              {title}
            </Typography.Text>
          </Space>
        </Link>
      ) : (
        <Typography.Text ellipsis style={{ maxWidth: 130 }}>
          {title}
        </Typography.Text>
      )}

      {isHovering ? children : null}
    </StyledNavigationHeader>
  );
};

export const NavbarBody = ({ children }: { children: React.ReactNode }) => {
  return <StyledNavigationBody>{children}</StyledNavigationBody>;
};
