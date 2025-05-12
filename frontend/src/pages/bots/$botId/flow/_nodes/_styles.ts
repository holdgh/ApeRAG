import { Avatar, GlobalToken, Typography } from 'antd';
import alpha from 'color-alpha';
import { css, styled } from 'umi';

export const StyledFlowNodeContainer = styled('div').withConfig({
  shouldForwardProp: (prop) =>
    !['token', 'color', 'selected', 'isHovering'].includes(prop),
})<{
  token: GlobalToken;
  color?: string;
  selected?: boolean;
  isHovering?: boolean;
}>`
  ${({ selected, token, color, isHovering = false }) => {
    return css`
      border-radius: 8px;
      color: ${token.colorText};
      border-color: ${selected ? color : token.colorBorder};
      border-width: 1px;
      border-style: solid;
      background: ${token.colorBgContainer};
      height: 100%;
      min-width: 260px;
      overflow: auto;
      transition:
        border-color 0.3s,
        box-shadow 0.3s;
      box-shadow: ${token.boxShadow};
      z-index: ${isHovering || selected ? 1 : 0};
      &:before {
        content: ' ';
        position: absolute;
        left: 0px;
        top: 0px;
        bottom: 0px;
        right: 0px;
        border-radius: 8px;
        border: 2px solid ${selected ? color : 'transparent'};
        transition: border-color 0.3s;
      }
      .react-flow__handle {
        width: 9px;
        height: 9px;
        border-radius: 9px;
        transition:
          border-color 0.3s,
          background 0.3s,
          width 0.3s,
          height 0.3s;
        border-width: 1px;
        background: ${token.colorBgContainer};
        border-color: ${selected ? color : token.colorBorder};
        &.node-handler-end {
          cursor: pointer;
          &:after {
            transition: all 0.3s;
            text-align: center;
            display: block;
            content: '+';
            line-height: 0;
            opacity: 0;
            color: ${token.colorWhite};
            transform: translate(0px, 2px);
          }
        }
      }

      &:hover {
        box-shadow: ${token.boxShadow};
        border-color: ${color};
        &:before {
          border-color: ${color};
        }
        .react-flow__handle {
          border-color: ${color};
        }
        .node-handler-end {
          width: 18px;
          height: 18px;
          background-color: ${color};
          &:after {
            font-size: 14px;
            opacity: 1;
            transform: translate(0px, 7px);
          }
        }
      }
    `;
  }}
`;

export const StyledFlowNode = styled('div').withConfig({})`
  ${() => {
    return css`
      height: 100%;
      display: flex;
      flex-direction: column;
      position: relative;
      cursor: default;
    `;
  }}
`;

export const StyledFlowNodeHeader = styled('div').withConfig({
  shouldForwardProp: (prop) => !['token'].includes(prop),
})<{
  token: GlobalToken;
}>`
  ${() => {
    return css`
      flex: auto;
      display: flex;
      justify-content: space-between;
      padding: 12px;
      cursor: move;
    `;
  }}
`;

export const StyledFlowNodeBody = styled('div').withConfig({
  shouldForwardProp: (prop) => !['collapsed', 'token'].includes(prop),
})<{ collapsed: boolean; token: GlobalToken }>`
  ${({ collapsed }) => {
    return css`
      margin: 12px;
      display: ${collapsed ? 'none' : 'block'};
    `;
  }}
`;

export const StyledFlowNodeAvatar = styled(Avatar).withConfig({
  shouldForwardProp: (prop) => !['color', 'token'].includes(prop),
})<{
  token: GlobalToken;
  color?: string;
}>`
  ${({ token, color = token.colorPrimary }) => {
    return css`
      background: linear-gradient(180deg, ${alpha(color, 0.75)}, ${color});
      > .anticon {
        font-size: 18px;
      }
    `;
  }}
`;

export const StyledFlowNodeLabel = styled(Typography.Text).withConfig({
  shouldForwardProp: (prop) => !['token'].includes(prop),
})<{
  token: GlobalToken;
}>`
  ${({}) => {
    return css`
      font-weight: bold;
      max-width: 120px;
      display: block;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    `;
  }}
`;

export const StyledFlowNodeSection = styled('section').withConfig({
  shouldForwardProp: (prop) => !['token'].includes(prop),
})<{
  token: GlobalToken;
}>`
  ${({ token }) => {
    return css`
      padding: 12px;
      background: ${token.colorBgLayout};
      border-radius: 8px;
      margin-bottom: 12px;
    `;
  }}
`;

export const getCollapsePanelStyle = (
  token: GlobalToken,
): React.CSSProperties => ({
  marginBottom: 12,
  background: token.colorBgLayout, // token.colorFillAlter,
  borderRadius: token.borderRadiusLG,
  border: 'none',
});
