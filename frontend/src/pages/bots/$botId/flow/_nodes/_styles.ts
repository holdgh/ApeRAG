import { Avatar, GlobalToken } from 'antd';
import alpha from 'color-alpha';
import { css, styled } from 'umi';
export const StyledFlowNode = styled('div').withConfig({
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
      min-width: 200px;
      min-height: 40px;
      padding: 12px;
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
