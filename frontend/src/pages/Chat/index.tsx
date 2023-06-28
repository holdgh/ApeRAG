import type { Chat, ChatSocketStatus } from '@/models/chat';
import { getUser } from '@/models/user';
import {
  CreateCollectionChat,
  GetCollectionChats,
  UpdateCollectionChat,
} from '@/services/chats';
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
  const [chatSocket, setChatSocket] = useState<WebSocket>();
  const [chatSocketStatus, setChatSocketStatus] =
    useState<ChatSocketStatus>('Closed');
  const { currentCollection } = useModel('collection');
  const { initialState } = useModel('@@initialState');
  const user = getUser();

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

  const createWebSocket = async () => {
    if (!currentCollection || !chat) return;

    const protocol = API_ENDPOINT.indexOf('https') > -1 ? 'wss' : 'ws';
    const host = API_ENDPOINT.replace(/^(http|https):\/\//, '');
    const prefix = `${protocol}://${host}`;
    const path = `/api/v1/collections/${currentCollection.id}/chats/${chat.id}/connect`;
    const socket = new WebSocket(prefix + path, user?.__raw);

    setChatSocketStatus('Connecting');
    socket.onopen = () => {
      setChatSocketStatus('Connected');
    };
    socket.onclose = () => {
      setChatSocketStatus('Closed');
    };
    // socket.onerror = (e) => console.log(e);

    socket.onmessage = (e) => {
      const data = chat.history || [];
      setChat({
        ...chat,
        history: data.concat({
          role: 'robot',
          message: e.data,
        }),
      });
      setLoading(false);
    };

    setChatSocket(socket);
  };

  const onClear = async () => {
    if (!currentCollection || !chat) return;
    const { data } = await UpdateCollectionChat(
      currentCollection?.id,
      chat?.id,
      {
        ...chat,
        history: [],
      },
    );
    if (data.id) {
      setChat(data);
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
    chatSocket?.send(msg);
    setTimeout(() => setLoading(true), 550);
  };

  useEffect(() => {
    return () => {
      chatSocket?.close();
    };
  }, [chatSocket]);

  useEffect(() => {
    getChats();
  }, [currentCollection]);

  useEffect(() => {
    createWebSocket();
  }, [chat]);

  return (
    <div
      className={classNames({
        [styles.chatContainer]: true,
        [styles.collapsed]: initialState?.collapsed,
      })}
    >
      <Header chat={chat} />
      <Content chat={chat} loading={loading} />
      <Footer
        status={chatSocketStatus}
        loading={loading}
        onSubmit={onSubmit}
        onClear={onClear}
      />
    </div>
  );
};
