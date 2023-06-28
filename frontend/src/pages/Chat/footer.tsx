import { MessageStatus, SocketStatus } from '@/models/chat';
import {
  ArrowRightOutlined,
  ClearOutlined,
  LoadingOutlined,
} from '@ant-design/icons';
import { Button, Input } from 'antd';
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
  const disabled = messageStatus !== 'normal' || socketStatus !== 'Connected';
  // const disabled = false;

  const _onSubmit = () => {
    const reg = new RegExp(/^\n+$/);
    if (message && !reg.test(message) && !disabled) {
      onSubmit(message);
      setMessage('');
    }
  };

  return (
    <div className={styles.footer}>
      <div className={styles.wrap}>
        <Button
          type="text"
          size="large"
          onClick={() => onClear()}
          icon={<ClearOutlined />}
          shape="circle"
        />
        <Input.TextArea
          className={styles.input}
          value={message}
          onChange={(e) => setMessage(e.currentTarget.value)}
          onPressEnter={(e) => {
            if (!e.shiftKey) {
              _onSubmit();
              e.preventDefault();
            }
          }}
          autoFocus
          autoSize={{ maxRows: 6 }}
          placeholder="Enter your question here..."
        />
        <Button
          type="primary"
          size="large"
          onClick={() => _onSubmit()}
          shape="circle"
          loading={disabled}
          icon={<ArrowRightOutlined />}
        />
      </div>
    </div>
  );
};
