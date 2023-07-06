import type { TypesMessage, TypesSocketStatus } from '@/types';
import { useModel } from '@umijs/max';
import { useEffect } from 'react';
import { animateScroll } from 'react-scroll';
import styles from './index.less';
import MessageItem from './msg';

type Props = {
  status: TypesSocketStatus;
  loading: boolean;
  onExecute: (msg: TypesMessage) => void;
};

export default ({ loading, onExecute, status }: Props) => {
  const { currentChat, chatLoading } = useModel('chat');
  const messages = currentChat?.history || [];

  useEffect(() => {
    animateScroll.scrollToBottom({
      duration: 0,
    });
    return () => {
      animateScroll.scrollToTop({
        duration: 0,
      });
    };
  }, [currentChat]);

  if (chatLoading) {
    return null;
  }

  return (
    <div id={`chats-container`} className={styles.content}>
      {messages.map((item, key) => {
        return (
          <MessageItem
            onExecute={onExecute}
            loading={
              (loading && key === messages.length - 1 && item.role === 'ai') ||
              chatLoading
            }
            status={status}
            key={key}
            item={item}
          />
        );
      })}
    </div>
  );
};
