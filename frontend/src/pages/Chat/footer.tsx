import { MessageStatus, SocketStatus } from '@/models/chat';
import {
  ClearOutlined,
  LoadingOutlined,
  SendOutlined,
} from '@ant-design/icons';
import { Button, Input, Space, Tooltip, Typography, theme } from 'antd';
import { useState } from 'react';
import styles from './index.less';

type Props = {
  socketStatus: SocketStatus;
  messageStatus: MessageStatus;
  onSubmit: (val: string) => void;
  onClear: () => void;
};

export default ({
  socketStatus,
  messageStatus,
  onClear = () => {},
  onSubmit = () => {},
}: Props) => {
  const [message, setMessage] = useState<string>();
  const { token } = theme.useToken();

  const _onSubmit = () => {
    if (message) onSubmit(message);
    setMessage(undefined);
  };

  // const disabled = messageStatus !== 'normal' || socketStatus !== 'Connected';
  const disabled = false;
  return (
    <div
      className={styles.footer}
      style={{ borderTop: `1px solid ${token.colorBorderSecondary}` }}
    >
      <Input
        disabled={disabled}
        value={message}
        onChange={(e) => setMessage(e.currentTarget.value)}
        onPressEnter={() => _onSubmit()}
        suffix={
          <Space>
            <Tooltip title="Clear">
              <Button
                type="text"
                onClick={() => onClear()}
                icon={
                  <Typography.Text type="secondary">
                    <ClearOutlined />
                  </Typography.Text>
                }
              ></Button>
            </Tooltip>
            <Tooltip title="Send">
              <Button
                type="text"
                disabled={disabled}
                onClick={() => _onSubmit()}
                icon={
                  disabled ? (
                    <LoadingOutlined />
                  ) : (
                    <Typography.Text style={{ color: token.colorPrimary }}>
                      <SendOutlined />
                    </Typography.Text>
                  )
                }
              ></Button>
            </Tooltip>
          </Space>
        }
        autoFocus
        size="large"
        bordered={false}
        placeholder="Enter your question here..."
      />
    </div>
  );
};
