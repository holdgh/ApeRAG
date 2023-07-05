import type { TypesMessage, TypesSocketStatus } from '@/types';
import { WechatFilled } from '@ant-design/icons';
import { useModel } from '@umijs/max';
import { Result, Typography } from 'antd';
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
      {messages.length === 0 ? (
        <Result
          style={{ marginTop: 100 }}
          icon={
            <Typography.Text>
              <WechatFilled style={{ opacity: 0.05, fontSize: 200 }} />
            </Typography.Text>
          }
        />
      ) : (
        messages.map((item, key) => {
          return (
            <MessageItem
              onExecute={onExecute}
              loading={
                loading && key === messages.length - 1 && item.role === 'ai'
              }
              status={status}
              key={key}
              item={item}
            />
          );
        })
      )}
    </div>
  );
};
