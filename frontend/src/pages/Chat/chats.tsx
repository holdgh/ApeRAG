import type { TypesMessage, TypesSocketStatus } from '@/types';
import { useModel } from '@umijs/max';
import { useEffect } from 'react';
import { Element as ScrollElement, scroller } from 'react-scroll';
import styles from './index.less';
import MessageItem from './msg';

type Props = {
  status: TypesSocketStatus;
  loading: boolean;
  onExecute: (msg: TypesMessage) => void;
};

export default ({ loading, onExecute, status }: Props) => {
  const { currentChat } = useModel('collection');
  const messages = currentChat?.history || [];

  useEffect(() => {
    scroller.scrollTo('bottom', {
      containerId: 'chat-content',
      smooth: true,
      duration: 800,
    });
  }, [currentChat]);

  return (
    <div id="chat-content" className={styles.content}>
      <div className={styles.wrap}>
        {messages.map((item, key) => {
          return (
            <MessageItem
              onExecute={onExecute}
              loading={loading && key === messages.length - 1 && item.role === 'ai'}
              status={status}
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
