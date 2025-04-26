import { ArrowLeftOutlined } from '@ant-design/icons';
import { useHover } from 'ahooks';
import { Button, GlobalToken, Space, theme, Typography } from 'antd';
import { useRef } from 'react';
import { css, Link, styled } from 'umi';

const StyledNavigation = styled('div')`
  ${() => {
    return css`
      display: flex;
      flex-direction: column;
      height: 100%;
    `;
  }}
`;

const StyledNavigationHeader = styled('div').withConfig({
  shouldForwardProp: (prop) => !['token', 'hasBackTo'].includes(prop),
})<{
  token: GlobalToken;
  hasBackTo?: boolean;
}>`
  ${({ token, hasBackTo }) => {
    return css`
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: ${token.paddingXS}px;
      padding-left: ${hasBackTo ? token.paddingXS : token.paddingSM}px;
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

export const Navbar = ({ children }: { children: React.ReactNode }) => {
  return <StyledNavigation>{children}</StyledNavigation>;
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
    <StyledNavigationHeader hasBackTo={Boolean(backTo)} ref={ref} token={token}>
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
