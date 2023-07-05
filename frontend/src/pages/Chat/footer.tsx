import { TypesSocketStatus } from '@/types';
import { ArrowRightOutlined, ClearOutlined } from '@ant-design/icons';
import { Button, Input } from 'antd';
import { useState } from 'react';
import styles from './index.less';

type Props = {
  loading: boolean;
  status: TypesSocketStatus;
  onSubmit: (val: string) => void;
  onClear: () => void;
};

export default ({
  loading,
  status,
  onClear = () => {},
  onSubmit = () => {},
}: Props) => {
  const [message, setMessage] = useState<string>('');

  const _onSubmit = () => {
    const reg = new RegExp(/^\n+$/);
    if (message && !reg.test(message) && !loading && status === 'Open') {
      onSubmit(message);
      setMessage('');
    }
  };

  return (
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
        loading={loading || status !== 'Open'}
        icon={<ArrowRightOutlined />}
      />
    </div>
  );
};
