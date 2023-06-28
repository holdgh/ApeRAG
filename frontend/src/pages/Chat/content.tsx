import { Chat, MessageStatus } from '@/models/chat';
import { useEffect } from 'react';
import { Element as ScrollElement, scroller } from 'react-scroll';
import styles from './index.less';
import Message from './message';

type Props = {
  chat?: Chat;
  messageStatus: MessageStatus;
};

export default ({ chat, messageStatus }: Props) => {
  useEffect(() => {
    if (chat) {
      scroller.scrollTo('bottom', {
        containerId: 'chat-content',
        smooth: true,
        duration: 100,
      });
    }
  }, [chat, messageStatus]);

  return (
    <div id="chat-content" className={styles.content}>
      <div className={styles.wrap}>
        {chat?.history?.map((item, key) => (
          <Message key={key} status="normal" item={item} />
        ))}
        {messageStatus !== 'normal' ? (
          <Message status={messageStatus} item={{ role: 'ai', data: '' }} />
        ) : null}
        <ScrollElement name="bottom"></ScrollElement>
      </div>
    </div>
  );
};
