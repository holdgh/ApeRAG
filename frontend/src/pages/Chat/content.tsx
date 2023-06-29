import { Chat } from '@/models/chat';
import { useEffect } from 'react';
import { Element as ScrollElement, scroller } from 'react-scroll';
import styles from './index.less';
import Message from './message';

type Props = {
  chat?: Chat;
};

export default ({ chat }: Props) => {
  useEffect(() => {
    if (chat) {
      scroller.scrollTo('bottom', {
        containerId: 'chat-content',
        smooth: true,
        duration: 300,
      });
    }
  }, [chat]);

  return (
    <div id="chat-content" className={styles.content}>
      <div className={styles.wrap}>
        {chat?.history?.map((item, key) => (
          <Message key={key} item={item} />
        ))}
        <ScrollElement name="bottom"></ScrollElement>
      </div>
    </div>
  );
};
