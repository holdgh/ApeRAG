import type { Chat } from '@/models/chat';
import { CreateCollectionChat, GetCollectionChats } from '@/services/chats';
import { useModel } from '@umijs/max';
import classNames from 'classnames';
import _ from 'lodash';
import { useEffect, useState } from 'react';
import Content from './content';
import Footer from './footer';
import Header from './header';
import styles from './index.less';

export default () => {
  const [loading, setLoading] = useState<boolean>(false);
  const [chat, setChat] = useState<Chat | undefined>();
  const { currentCollection } = useModel('collection');
  const { initialState } = useModel('@@initialState');

  const createChat = async () => {
    if (!currentCollection) return;
    await CreateCollectionChat(currentCollection?.id);
  };
  const getChats = async () => {
    if (!currentCollection) return;
    const { data } = await GetCollectionChats(currentCollection?.id);
    const item = _.first(data);
    if (item) {
      setChat(item);
    } else {
      await createChat();
      await getChats();
    }
  };

  const onSubmit = (msg: string) => {
    if (!chat) return;
    const data = chat.history || [];
    setChat({
      ...chat,
      history: data.concat({
        role: 'human',
        message: msg,
      }),
    });
    setTimeout(() => setLoading(true), 900);
  };

  const onClear = () => {};

  useEffect(() => {
    if (currentCollection) {
      getChats();
    }
  }, [currentCollection]);

  return (
    <div
      className={classNames({
        [styles.chatContainer]: true,
        [styles.collapsed]: initialState?.collapsed,
      })}
    >
      <Header chat={chat} />
      <Content chat={chat} loading={loading} />
      <Footer loading={loading} onSubmit={onSubmit} onClear={onClear} />
    </div>
  );
};
