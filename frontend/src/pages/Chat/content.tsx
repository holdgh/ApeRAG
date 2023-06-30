import { Message } from '@/models/chat';
import { useEffect } from 'react';
import { Element as ScrollElement, scroller } from 'react-scroll';
import styles from './index.less';
import MessageItem from './messageItem';

type Props = {
  messages: Message[];
  loading: boolean,
};

export default ({ messages, loading }: Props) => {
  useEffect(() => {
    scroller.scrollTo('bottom', {
      containerId: 'chat-content',
      smooth: true,
      duration: 300,
    });
  }, [messages]);

  

  return (
    <div id="chat-content" className={styles.content}>
      <div className={styles.wrap}>
        {messages.map((item, key) => {
          const isLoading = key === messages.length - 1 && loading;
          return <MessageItem loading={isLoading} key={key} item={item} />
        })}
        <ScrollElement name="bottom"></ScrollElement>
      </div>
    </div>
  );
};
