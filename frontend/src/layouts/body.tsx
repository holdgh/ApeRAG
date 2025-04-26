import { NAVIGATION_WIDTH, SIDEBAR_WIDTH, TOPBAR_HEIGHT } from '@/constants';
import { css, styled } from 'umi';

const StyledMainContainer = styled('main').withConfig({
  shouldForwardProp: (prop) => !['sidebar', 'navbar'].includes(prop),
})<{
  sidebar: boolean;
  navbar: boolean;
}>`
  ${({ sidebar, navbar }) => {
    let offsetLeft = 0;

    if (sidebar) offsetLeft += SIDEBAR_WIDTH;
    if (navbar) offsetLeft += NAVIGATION_WIDTH;

    return css`
      ${offsetLeft ? `padding-left: ${offsetLeft}px` : ''};
      padding-top: ${TOPBAR_HEIGHT}px;
      transition: all 0s;
    `;
  }}
`;

export const BodyContainer = ({
  sidebar,
  navbar,
  children,
}: {
  sidebar: boolean;
  navbar: boolean;
  children: React.ReactNode;
}) => {
  return (
    <StyledMainContainer sidebar={sidebar} navbar={navbar}>
      {children}
    </StyledMainContainer>
  );
};
