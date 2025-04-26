import { TOPBAR_HEIGHT } from '@/constants';
import { GlobalToken, theme } from 'antd';
import { CSSProperties } from 'react';
import { css, styled } from 'umi';

const StyledPageContainer = styled('div').withConfig({
  shouldForwardProp: (prop) =>
    !['height', 'token', 'padding', 'sidebar', 'width', 'maxWidth'].includes(
      prop,
    ),
})<{
  token: GlobalToken;
  height?: 'auto' | 'fixed';
  width?: 'auto' | 'fixed' | number;
  maxWidth?: number;
  padding?: boolean;
}>`
  ${({ height = 'auto', token, padding, width = 'fixed', maxWidth }) => {
    return css`
      position: relative;
      overflow: auto;
      ${padding ? `padding: ${token.paddingLG}px;` : ''}
      ${height === 'fixed' ? `height: calc(100vh - ${TOPBAR_HEIGHT}px);` : ''}
      ${width === 'fixed' ? 'max-width: 1200px;' : ''}
      ${width === 'fixed' ? 'margin-inline: auto;' : ''}
      ${maxWidth ? `max-width: ${maxWidth}px;` : ''}
    `;
  }}
`;

type PageContainerProps = {
  children?: React.ReactNode;
  height?: 'auto' | 'fixed';
  width?: 'auto' | 'fixed';
  maxWidth?: number;
  padding?: boolean;
  spinning?: boolean;
  style?: CSSProperties;
  loading?: boolean;
};

export const PageContainer = ({
  children,
  height = 'auto',
  width = 'fixed',
  maxWidth,
  padding = true,
  loading = false,
  style,
}: PageContainerProps) => {
  const { token } = theme.useToken();
  return (
    <StyledPageContainer
      token={token}
      height={height}
      width={width}
      maxWidth={maxWidth}
      padding={padding}
      style={style}
    >
      {!loading ? children : ''}
    </StyledPageContainer>
  );
};
