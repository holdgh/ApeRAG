import { NAVIGATION_WIDTH, SIDEBAR_WIDTH } from '@/constants';
import { SendOutlined } from '@ant-design/icons';
import { Button, GlobalToken, Input, theme, Typography } from 'antd';
import alpha from 'color-alpha';
import _ from 'lodash';
import { useState } from 'react';
import { css, styled, useIntl } from 'umi';

export const StyledChatInputContainer = styled('div').withConfig({
  shouldForwardProp: (prop) => !['token'].includes(prop),
})<{ token: GlobalToken }>`
  ${({ token }) => {
    return css`
      padding: 24px;
      position: fixed;
      left: ${SIDEBAR_WIDTH + NAVIGATION_WIDTH}px;
      bottom: 0;
      right: 0;
      backdrop-filter: blur(20px);
      background-color: ${alpha(token.colorBgLayout, 0.85)};
      display: flex;
      justify-content: center;
      align-items: center;
      gap: 12px;
    `;
  }}
`;

export const StyledChatInput = styled(Input).withConfig({
  shouldForwardProp: (prop) => !['token'].includes(prop),
})<{ token: GlobalToken }>`
  ${({ token }) => {
    return css`
      background: none !important;
      border-radius: 100px;
      padding: 8px 8px 8px 24px;
      width: 75%;
      box-shadow: ${token.boxShadow};
      border-color: ${token.colorPrimary};
    `;
  }}
`;

export const ChatInput = ({
  onSubmit,
  loading,
}: {
  onSubmit: (v: string) => void;
  loading?: boolean;
}) => {
  const { token } = theme.useToken();
  const [value, setValue] = useState<string>();
  const { formatMessage } = useIntl();

  const onPressEnter = async () => {
    const data = _.trim(value);
    if (loading || _.isEmpty(data)) return;
    onSubmit(data);
    setValue(undefined);
  };

  return (
    <StyledChatInputContainer token={token}>
      <StyledChatInput
        value={value}
        onChange={(e) => setValue(e.currentTarget.value)}
        token={token}
        onPressEnter={() => onPressEnter()}
        placeholder={formatMessage(
          { id: 'chat.input_placeholder' },
          { title: APERAG_CONFIG.title },
        )}
        autoFocus
        suffix={
          <Button
            loading={loading}
            type="text"
            shape="circle"
            onClick={() => onPressEnter()}
            icon={
              <Typography.Text type="secondary">
                <SendOutlined />
              </Typography.Text>
            }
          />
        }
      />
    </StyledChatInputContainer>
  );
};
