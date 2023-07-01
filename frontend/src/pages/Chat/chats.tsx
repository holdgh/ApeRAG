import type { TypesMessage, TypesSocketStatus } from '@/models/chat';
import { useModel } from '@umijs/max';
import { useEffect } from 'react';
import { Element as ScrollElement, scroller } from 'react-scroll';
import styles from './index.less';
import MessageItem from './msg';

type Props = {
  status: TypesSocketStatus;
  loading: boolean;
  onExecuteSQL: (msg?: TypesMessage) => void;
};

export default ({ loading, status, onExecuteSQL }: Props) => {
  const { currentChat } = useModel('collection');

  const messages = currentChat?.history || [];

  useEffect(() => {
    scroller.scrollTo('bottom', {
      containerId: 'chat-content',
      smooth: true,
      duration: 300,
    });
  }, [messages, loading]);

  return (
    <div id="chat-content" className={styles.content}>
      <div className={styles.wrap}>
        {messages.map((item, key) => {
          const isLoading =
            key === messages.length - 1 && loading && status === 'Open';
          return (
            <MessageItem
              animate={
                loading && item.role === 'ai' && key === messages.length - 1
              }
              disabled={loading}
              onExecuteSQL={onExecuteSQL}
              loading={isLoading}
              key={key}
              item={item}
            />
          );
        })}
        <ScrollElement name="bottom"></ScrollElement>
      </div>
    </div>
  );
};
