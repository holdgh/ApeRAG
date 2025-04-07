import { TypesSocketStatus } from '@/types';
import { useIntl } from '@umijs/max';
import { Input } from 'antd';
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
  const isLoading = isTyping || status !== 'Open';
  const _onSubmit = () => {
    const reg = new RegExp(/^\n+$/);
    if (message && !reg.test(message) && !isLoading) {
      onSubmit(message.replace(/\n+$/, ''));
      setMessage('');
    }
  };

  const intl = useIntl();

  return (
    <div className={styles.wrap}>
      <i className="clear-icon" title={intl.formatMessage({id:'bots.chat.clear'})} onClick={() => onClear()}></i>

      <div className={styles.inputWrap}>
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
          placeholder={intl.formatMessage({id:'bots.chat.placeholder'})}
        />

        <i className="send-icon" title={intl.formatMessage({id:'bots.chat.send'})} onClick={() => _onSubmit()}></i>
      </div>
    </div>
  );
};
