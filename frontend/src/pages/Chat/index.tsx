import type { Chat, Message, MessageStatus, SocketStatus } from '@/models/chat';
import { getUser } from '@/models/user';
import {
  CreateCollectionChat,
  GetCollectionChat,
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
  const [chat, setChat] = useState<Chat | undefined>();
  const [chatSocket, setChatSocket] = useState<WebSocket>();
  const [socketStatus, setSocketStatus] = useState<SocketStatus>('Closed');
  const [messageStatus, setMessageStatus] = useState<MessageStatus>('normal');
  const [pingTimer, setPingTimer] = useState<NodeJS.Timer>();
  const { currentCollection } = useModel('collection');
  const { initialState } = useModel('@@initialState');
  const user = getUser();

  const createChat = async () => {
    if (!currentCollection) return;
    await CreateCollectionChat(currentCollection?.id);
  };
  const getChat = async (id: number) => {
    if (!currentCollection) return;
    const { data } = await GetCollectionChat(currentCollection.id, id);
    setChat(data);
  };

  const getChats = async () => {
    if (!currentCollection) return;
    const { data } = await GetCollectionChats(currentCollection?.id);
    const item = _.first(data);
    if (item) {
      getChat(item.id);
    } else {
      await createChat();
      await getChats();
    }
  };

  const createWebSocket = async () => {
    if (!currentCollection || !chat || chatSocket) return;
    const protocol = API_ENDPOINT.indexOf('https') > -1 ? 'wss' : 'ws';
    const host = API_ENDPOINT.replace(/^(http|https):\/\//, '');
    const prefix = `${protocol}://${host}`;
    const path = `/api/v1/collections/${currentCollection.id}/chats/${chat.id}/connect`;
    const socket = new WebSocket(prefix + path, user?.__raw);

    setSocketStatus('Connecting');
    setChatSocket(socket);

    // socket.onerror = (e) => console.log(e);
    socket.onopen = () => {
      setSocketStatus('Connected');
      const pingMsg: Message = {
        type: 'ping',
      };
      const timer = setInterval(
        () => socket.send(JSON.stringify(pingMsg)),
        5000,
      );
      setPingTimer(timer);
    };
    socket.onclose = () => {
      setSocketStatus('Closed');
    };
    socket.onmessage = (e) => {
      let msg: Message = {};
      try {
        msg = JSON.parse(e.data);
      } catch (err) {}

      if (msg.error) {
        setMessageStatus('error');
      } else if (msg.type === 'message' && msg.data) {
        setChat((state) => {
          if (state) {
            return {
              ...state,
              history: (state.history || []).concat({ ...msg, role: 'ai' }),
            };
          }
        });
        setMessageStatus('normal');
      }
    };
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

  const onSubmit = async (data: string) => {
    if (!chat) return;
    const timestamp = new Date().getTime();
    const msg: Message = {
      type: 'message',
      role: 'human',
      data,
      timestamp,
    };
    
    setChat((state) => {
      if (state) {
        return {
          ...state,
          history: (state.history || []).concat(msg)
        };
      }
    });
    setMessageStatus('loading');
    chatSocket?.send(JSON.stringify(msg));
  };

  useEffect(() => {
    return () => chatSocket?.close();
  }, [chatSocket]);

  useEffect(() => {
    return () => clearInterval(pingTimer);
  }, [pingTimer]);

  useEffect(() => {
    if (socketStatus !== 'Closed') return;
    clearInterval(pingTimer);
  }, [socketStatus]);

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
      <Content chat={chat} messageStatus={messageStatus} />
      <Footer
        socketStatus={socketStatus}
        messageStatus={messageStatus}
        onSubmit={onSubmit}
        onClear={onClear}
      />
    </div>
  );
};
