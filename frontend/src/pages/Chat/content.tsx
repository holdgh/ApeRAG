import { Chat, MessageStatus } from '@/models/chat';
import { useEffect } from 'react';
import { Element as ScrollElement, scroller } from 'react-scroll';
import { CSSTransition, TransitionGroup } from 'react-transition-group';
import './animate.css';
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
        containerId: 'chart-content',
      });
    }
  }, [chat, messageStatus]);

  return (
    <div id="chart-content" className={styles.content}>
      <TransitionGroup>
        {chat?.history?.map((item, key) => (
          <CSSTransition key={key} timeout={500} classNames="animate-item">
            <Message status="normal" item={item} />
          </CSSTransition>
        ))}
        {messageStatus !== 'normal' ? (
          <CSSTransition timeout={500} classNames="animate-item">
            <Message
              status={messageStatus}
              item={{ role: 'ai', message: '' }}
            />
          </CSSTransition>
        ) : null}
      </TransitionGroup>
      <ScrollElement name="bottom"></ScrollElement>
    </div>
  );
};
