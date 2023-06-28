import { Chat } from '@/models/chat';
import { useEffect } from 'react';
import { Element as ScrollElement, scroller } from 'react-scroll';
import { CSSTransition, TransitionGroup } from 'react-transition-group';
import './animate.css';
import styles from './index.less';
import Message from './message';

type Props = {
  chat?: Chat;
  loading?: boolean;
};

export default ({ chat, loading = false }: Props) => {
  useEffect(() => {
    if (chat) {
      scroller.scrollTo('bottom', {
        containerId: 'chart-content',
      });
    }
  }, [chat, loading]);

  return (
    <div id="chart-content" className={styles.content}>
      <TransitionGroup>
        {chat?.history?.map((item, key) => (
          <CSSTransition key={key} timeout={500} classNames="animate-item">
            <Message loading={false} item={item} />
          </CSSTransition>
        ))}
        {loading ? (
          <CSSTransition timeout={500} classNames="animate-item">
            <Message loading={true} item={{ role: 'robot', message: '' }} />
          </CSSTransition>
        ) : null}
      </TransitionGroup>
      <ScrollElement name="bottom"></ScrollElement>
    </div>
  );
};
