import { SIDEBAR_WIDTH, TOPBAR_HEIGHT } from '@/constants';
import { GlobalToken, theme, Tooltip } from 'antd';
import { BsChatText, BsFiletypeDoc, BsGear } from 'react-icons/bs';
import { css, Link, styled, useIntl, useLocation } from 'umi';
import UrlPattern from 'url-pattern';

const StyledSidebar = styled('aside').withConfig({
  shouldForwardProp: (prop) => !['token'].includes(prop),
})<{
  token: GlobalToken;
}>`
  ${({ token }) => {
    return css`
      width: ${SIDEBAR_WIDTH}px;
      overflow: auto;
      border-right: 1px solid ${token.colorBorderSecondary};
      position: fixed;
      text-align: center;
      left: 0px;
      top: ${TOPBAR_HEIGHT}px;
      bottom: 0;
      z-index: ${token.zIndexPopupBase};
      display: flex;
      justify-content: space-between;
      flex-direction: column;
      // background: ${token.colorBgContainer};
    `;
  }}
`;

const StyledSidebarLink = styled(Link).withConfig({
  shouldForwardProp: (prop) => !['token', 'active'].includes(prop),
})<{
  token: GlobalToken;
  active: boolean;
}>`
  ${({ token, active }) => {
    const gap = 6;
    const size = SIDEBAR_WIDTH - gap * 2;
    return css`
      color: ${active ? token.colorText : token.colorTextSecondary};
      background: ${active ? token.controlItemBgActive : 'none'};
      display: block;
      text-align: center;
      width: ${size}px;
      height: ${size}px;
      line-height: ${size}px;
      border-radius: ${gap}px;
      margin: ${gap}px;
      padding-top: 2px;
      font-size: 18px;
      transition: all 0.3s;
      &:hover {
        color: var(--ape-color-text);
        background: var(--ape-color-border-secondary);
      }
    `;
  }}
`;

export default () => {
  const { token } = theme.useToken();
  const { formatMessage } = useIntl();

  const location = useLocation();

  const sidebar_items = [
    {
      path: '/bots',
      icon: <BsChatText />,
    },
    {
      path: '/collections',
      icon: <BsFiletypeDoc />,
    },
  ];

  return (
    <StyledSidebar token={token}>
      <div>
        {sidebar_items.map((item, index) => {
          const pattern = new UrlPattern(`${item.path}*`);
          const active = pattern.match(location.pathname);
          return (
            <StyledSidebarLink
              key={index}
              token={token}
              active={active}
              to={item.path}
            >
              {item.icon}
            </StyledSidebarLink>
          );
        })}
      </div>
      <Tooltip
        title={formatMessage({ id: 'action.settings' })}
        placement="right"
      >
        <div>
          <StyledSidebarLink
            token={token}
            active={new UrlPattern(`/settings*`).match(location.pathname)}
            to="/settings"
          >
            <BsGear />
          </StyledSidebarLink>
        </div>
      </Tooltip>
    </StyledSidebar>
  );
};
