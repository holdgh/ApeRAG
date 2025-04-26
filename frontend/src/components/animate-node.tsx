import { GlobalToken } from 'antd';
import { CSSProperties, useRef } from 'react';
import { CSSTransition } from 'react-transition-group';
import { css, styled } from 'umi';

type AnimateNodeProps = {
  in?: boolean;
  type: 'fade';
  style?: CSSProperties;
  children: React.ReactNode;
};

const StyledCSSTransition = styled(CSSTransition).withConfig({
  shouldForwardProp: (prop) => !['token'].includes(prop),
})<{
  token: GlobalToken;
}>`
  ${({}) => {
    return css`
      &.enter {
        opacity: 0;
      }
      &.enter-done {
        opacity: 1;
        transition: opacity 0ms;
      }
      &.exit {
        opacity: 1;
      }
      &.exit-done {
        opacity: 0;
        transition: opacity 0ms;
      }
    `;
  }}
`;

export const AnimateNode = (props: AnimateNodeProps) => {
  const ref = useRef(null);
  return (
    <StyledCSSTransition in={props.in} nodeRef={ref} timeout={300}>
      <span style={props.style} ref={ref}>
        {props.children}
      </span>
    </StyledCSSTransition>
  );
};
