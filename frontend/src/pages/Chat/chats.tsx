import type { TypesMessage, TypesSocketStatus } from '@/types';
import { useModel, useParams } from '@umijs/max';
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
  const { currentChat } = useModel('chat');
  const messages = currentChat?.history || [];
  const { collectionId } = useParams();

  useEffect(() => {
    setTimeout(() => {
      animateScroll.scrollToBottom({
        duration: 0,
      });
    }, 100);
  }, [currentChat]);

  if (collectionId !== currentChat?.collectionId) {
    return null;
  }

  return (
    <div id={`chats-container`} className={styles.content}>
      {messages.map((item, key) => {
        return (
          <MessageItem
            onExecute={onExecute}
            isTyping={
              loading &&
              key === messages.length - 1 &&
              item.role === 'ai' &&
              status === 'Open'
            }
            key={key}
            item={item}
          />
        );
      })}
    </div>
  );
};
