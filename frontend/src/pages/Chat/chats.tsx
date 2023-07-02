import type { TypesMessage, TypesSocketStatus } from '@/types';
import { useModel } from '@umijs/max';
import _ from 'lodash';
import { useEffect } from 'react';
import { Element as ScrollElement, scroller } from 'react-scroll';
import styles from './index.less';
import MessageItem from './msg';

type Props = {
  status: TypesSocketStatus;
  loading: boolean;
  onExecuteSQL: (msg?: TypesMessage) => void;
};

export default ({ loading, onExecuteSQL, status }: Props) => {
  const { currentChat } = useModel('collection');

  const messages = currentChat?.history || [];

  useEffect(() => {
    scroller.scrollTo('bottom', {
      containerId: 'chat-content',
      smooth: true,
      duration: 0,
    });
  }, [currentChat]);

  const lastAiIndex = _.findLastIndex(
    messages,
    (m: TypesMessage) => m.role === 'ai',
  );
  return (
    <div id="chat-content" className={styles.content}>
      <div className={styles.wrap}>
        {messages.map((item, key) => {
          const isLoading = key === lastAiIndex && loading;
          return (
            <MessageItem
              animate={
                item.role === 'ai' &&
                key === messages.length - 1 &&
                loading &&
                status === 'Open'
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
