import { ChatMessage } from '@/api';
import { ApeMarkdown } from '@/components';
import { TypingAnimate } from '@/components/typing-animate';
import { DATETIME_FORMAT } from '@/constants';
import {
  BulbOutlined,
  CaretRightOutlined,
  DislikeFilled,
  LikeFilled,
  UserOutlined,
} from '@ant-design/icons';
import { useHover } from 'ahooks';
import {
  Avatar,
  Badge,
  Button,
  Collapse,
  CollapseProps,
  Drawer,
  GlobalToken,
  Space,
  theme,
  Tooltip,
  Typography,
} from 'antd';
import _ from 'lodash';
import moment from 'moment';
import { useRef, useState } from 'react';
import { BsRobot } from 'react-icons/bs';
import { css, styled, useIntl } from 'umi';

export const StyledMessage = styled('div').withConfig({
  shouldForwardProp: (prop) => !['message'].includes(prop),
})<{ message: ChatMessage }>`
  ${({ message }) => {
    return css`
      display: flex;
      flex-direction: row;
      justify-content: ${message.role === 'human' ? 'flex-end' : 'flex-start'};
      margin-bottom: 24px;
      gap: 12px;
      min-width: 240px;
    `;
  }}
`;

export const StyledMessageAvatar = styled(Avatar).withConfig({
  shouldForwardProp: (prop) => !['token'].includes(prop),
})<{ token: GlobalToken }>`
  ${({ token }) => {
    return css`
      background: ${token.colorPrimary};
      margin-top: 8px;
      box-shadow: ${token.boxShadow};
    `;
  }}
`;

export const StyledMessageBody = styled('div')`
  ${() => {
    return css`
      max-width: 75%;
      min-width: 25%;
      display: flex;
      flex-direction: column;
      gap: 4px;
    `;
  }}
`;

export const StyledMessageContent = styled('div').withConfig({
  shouldForwardProp: (prop) => !['message', 'token'].includes(prop),
})<{ message: ChatMessage; token: GlobalToken }>`
  ${({ message, token }) => {
    return css`
      background: ${message.role === 'human'
        ? token.colorPrimary
        : token.colorBgContainer};
      color: ${message.role === 'human' ? token.colorWhite : token.colorText};
      min-height: 54px;
      padding: 16px;
      border-radius: 8px;
      box-shadow: ${token.boxShadow};
      .hljs {
        border-radius: 4px;
        font-size: 12px;
      }
    `;
  }}
`;

export const StyledMessageInfo = styled('div').withConfig({
  shouldForwardProp: (prop) => !['token', 'message'].includes(prop),
})<{ token: GlobalToken; message: ChatMessage }>`
  ${({ token, message }) => {
    return css`
      color: ${token.colorTextSecondary};
      display: flex;
      justify-content: space-between;
      font-size: 12px;
      gap: 16px;
      align-items: center;
      min-height: 32px;
      justify-content: ${message.role === 'human' ? 'flex-end' : 'flex-start'};
    `;
  }}
`;

export const ChatMessageItem = ({
  item,
  loading,
  onVote,
}: {
  item: ChatMessage;
  loading: boolean;
  onVote: (item: ChatMessage, like: boolean) => void;
}) => {
  const { token } = theme.useToken();
  const hoverRef = useRef(null);
  const isHovering = useHover(hoverRef);
  const { formatMessage } = useIntl();
  const [referencesVisible, setReferencesVisible] = useState<boolean>(false);

  const getReferences: () => CollapseProps['items'] = () =>
    item.references?.map((reference, index) => ({
      key: index,
      label: (
        <Typography.Text
          style={{ maxWidth: 400, color: token.colorPrimary }}
          ellipsis
        >
          {index + 1}. {reference.metadata?.name || reference.metadata?.source}
        </Typography.Text>
      ),
      children: (
        <div
          style={{
            borderTop: `1px solid ${token.colorBorderSecondary}`,
            paddingTop: 16,
          }}
        >
          <ApeMarkdown>{reference.text}</ApeMarkdown>
        </div>
      ),
      extra: (
        <Space>
          <BulbOutlined />
          {reference.score}
        </Space>
      ),
      style: {
        marginBottom: 24,
        borderRadius: token.borderRadiusLG,
        border: `1px solid ${token.colorBorderSecondary}`,
      },
    }));

  return (
    <>
      <StyledMessage message={item}>
        {item.role === 'ai' && (
          <StyledMessageAvatar src={<BsRobot />} size="large" token={token} />
        )}
        <StyledMessageBody ref={hoverRef}>
          <StyledMessageContent token={token} message={item}>
            {item.role === 'human' ? (
              item.data
            ) : loading ? (
              <TypingAnimate />
            ) : (
              <ApeMarkdown>{item.data}</ApeMarkdown>
            )}
          </StyledMessageContent>
          <StyledMessageInfo token={token} message={item}>
            {moment(item.timestamp).format(DATETIME_FORMAT)}
            {!_.isEmpty(item.references) && item.role === 'ai' && (
              <Tooltip title={formatMessage({ id: 'text.references' })}>
                <Button
                  type="text"
                  onClick={() => setReferencesVisible(true)}
                  icon={
                    <Badge
                      count={_.size(item.references)}
                      size="small"
                      style={{ marginTop: -2 }}
                    />
                  }
                />
              </Tooltip>
            )}
            {isHovering && item.role === 'ai' ? (
              <Space>
                <Button
                  icon={
                    <LikeFilled
                      style={{
                        color: item.upvote
                          ? token.colorSuccess
                          : token.colorTextDisabled,
                      }}
                    />
                  }
                  type="text"
                  onClick={() => onVote(item, true)}
                />
                <Button
                  icon={
                    <DislikeFilled
                      style={{
                        color: item.downvote
                          ? token.colorError
                          : token.colorTextDisabled,
                      }}
                    />
                  }
                  type="text"
                  onClick={() => onVote(item, false)}
                />
              </Space>
            ) : null}
          </StyledMessageInfo>
        </StyledMessageBody>
        {item.role === 'human' && (
          <StyledMessageAvatar
            size="large"
            token={token}
            icon={<UserOutlined style={{ fontSize: 14 }} />}
          />
        )}
      </StyledMessage>
      <Drawer
        title={formatMessage({ id: 'text.references' })}
        open={referencesVisible}
        size="large"
        onClose={() => setReferencesVisible(false)}
      >
        <Collapse
          bordered={false}
          defaultActiveKey={['0']}
          expandIcon={({ isActive }) => (
            <CaretRightOutlined rotate={isActive ? 90 : 0} />
          )}
          style={{ background: token.colorBgContainer }}
          items={getReferences()}
        />
      </Drawer>
    </>
  );
};
