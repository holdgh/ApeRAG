import { MessageStatus, SocketStatus } from '@/models/chat';
import {
  ClearOutlined,
  LoadingOutlined,
  SendOutlined,
} from '@ant-design/icons';
import { Button, Input, Typography, theme } from 'antd';
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
  const [message, setMessage] = useState<string>('');
  const { token } = theme.useToken();
  const disabled = messageStatus !== 'normal' || socketStatus !== 'Connected';
  // const disabled = false;

  const _onSubmit = () => {
    const reg = new RegExp(/^\n+$/);
    if (message && !reg.test(message) && !disabled) {
      onSubmit(message);
      setMessage('');
    };
  };
  
  return (
    <div className={styles.footer}>
      <Button
        type="text"
        size="large"
        onClick={() => onClear()}
        icon={<ClearOutlined />}
      />
      <Input.TextArea
        className={styles.input}
        value={message}
        size="large"
        onChange={(e) => setMessage(e.currentTarget.value)}
        onPressEnter={(e) => {
          if (!e.shiftKey) _onSubmit();
        }}
        autoFocus
        autoSize
        placeholder="enter your question here..."
      />
      <Button
        type="text"
        size="large"
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
      />
    </div>
  );
};
