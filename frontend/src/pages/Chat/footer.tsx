import { TypesSocketStatus } from '@/types';
import { ArrowRightOutlined, ClearOutlined } from '@ant-design/icons';
import { useModel } from '@umijs/max';
import { Button, Input } from 'antd';
import { useState } from 'react';
import styles from './index.less';

type Props = {
  isTyping: boolean;
  status: TypesSocketStatus;
  disabled: boolean;
  onSubmit: (val: string) => void;
  onClear: () => void;
};

export default ({
  isTyping,
  status,
  disabled = false,
  onClear = () => {},
  onSubmit = () => {},
}: Props) => {
  const [message, setMessage] = useState<string>('');
  const { databaseLoading } = useModel('database');

  const isLoading = isTyping || databaseLoading || status !== 'Open';

  const _onSubmit = () => {
    const reg = new RegExp(/^\n+$/);
    if (message && !reg.test(message) && !isLoading) {
      onSubmit(message.replace(/\n+$/, ''));
      setMessage('');
    }
  };

  return (
    <div className={styles.wrap}>
      <Button
        type="text"
        size="large"
        disabled={disabled}
        onClick={() => onClear()}
        icon={<ClearOutlined />}
        shape="circle"
      />
      <Input.TextArea
        className={styles.input}
        value={message}
        disabled={disabled}
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
        disabled={disabled}
        onClick={() => _onSubmit()}
        shape="circle"
        loading={isLoading}
        icon={<ArrowRightOutlined />}
      />
    </div>
  );
};
