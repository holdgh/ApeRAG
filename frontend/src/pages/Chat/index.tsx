import type { Chat, Message, SocketStatus } from '@/models/chat';
import { getUser } from '@/models/user';
import {
  CreateCollectionChat,
  GetCollectionChat,
  GetCollectionChats,
  UpdateCollectionChat,
} from '@/services/chats';
import useWebSocket, { ReadyState } from 'react-use-websocket';
import { RouteContext, RouteContextType } from '@ant-design/pro-components';
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
  const { currentCollection } = useModel('collection');
  const [socket, setSocket] = useState<WebSocket>();
  const [status, setStatus] = useState<SocketStatus>('Closed');
  const [loading, setLoading] = useState<boolean>(false);
  const [pingTimer, setPingTimer] = useState<NodeJS.Timer>();
  const { initialState } = useModel('@@initialState');
  const user = getUser();


  const createChat = async () => {
    if (!currentCollection) return;
    const { data } = await CreateCollectionChat(currentCollection?.id);
    setChat(data);
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
    }
  };

  const onMessage = (e) => {
    let msg: Message = {};
      try {
        msg = JSON.parse(e.data);
      } catch (err) {}

      if (msg.type === 'pong') {
        return;
      }

      if (msg.type === 'error') {
        return;
      }

      if (msg.type === 'stop') {
        setLoading(false);
        return;
      }

      if (msg.type === 'message' && msg.data) {
        console.log(loading, 111)
        // setChat((state) => {
        //   if (!state) return;
        //   const history = _.cloneDeep(state.history || []);
        //   const message: Message = { ...msg, role: 'ai' };
        //   let lastAiIndex = _.findLastIndex(history, (h) => h.role === 'ai');

        //   if(lastAiIndex === -1) {
        //     history.push(message);
        //   } else {
        //     if (loading) {
        //       _.update(history, lastAiIndex, (origin) => ({
        //         ...message,
        //         data: origin?.data || '' + message.data,
        //       }));
        //     } else {
        //       history.push(message);
        //     }
        //   }
        //   return { ...state, history };
        // });
      }
  }

  const createWebSocket = async () => {
    if (!currentCollection || !chat || socket) return;
    const protocol = API_ENDPOINT.indexOf('https') > -1 ? 'wss' : 'ws';
    const host = API_ENDPOINT.replace(/^(http|https):\/\//, '');
    const prefix = `${protocol}://${host}`;
    const path = `/api/v1/collections/${currentCollection.id}/chats/${chat.id}/connect`;
    const socketClient = new WebSocket(prefix + path, user?.__raw);

    setStatus('Connecting');
    setSocket(socketClient);

    // socketClient.onerror = (e) => console.log(e);
    socketClient.onopen = function() {
      setStatus('Connected');
      const pingMsg: Message = { type: 'ping' };
      const timer = setInterval(
        () => socketClient.send(JSON.stringify(pingMsg)),
        10000,
      );
      setPingTimer(timer);
    };
    socketClient.onclose = function() {
      setStatus('Closed');
    };
    socketClient.onmessage = onMessage
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
    if (!chat || !socket) return;
    const timestamp = new Date().getTime();
    const msg: Message = {
      type: 'message',
      role: 'human',
      data,
      timestamp,
    };
    setChat((state) => {
      if (!state) return;
      const history = state.history || [];
      return { ...state, history: history.concat(msg) };
    });
    setLoading(true);
    setTimeout(() => {
      socket.send(JSON.stringify(msg));
    }, 1000);
  };

  useEffect(() => {
    return () => socket?.close();
  }, [socket]);

  useEffect(() => {
    return () => clearInterval(pingTimer);
  }, [pingTimer]);

  useEffect(() => {
    if (status !== 'Closed') return;
    clearInterval(pingTimer);
  }, [status]);

  useEffect(() => {
    getChats();
  }, [currentCollection]);

  useEffect(() => {
    createWebSocket();
  }, [chat]);

  return (
    <RouteContext.Consumer>
      {(value: RouteContextType) => {
        const { isMobile } = value;
        return (
          <div
            className={classNames({
              [styles.container]: true,
              [styles.collapsed]: initialState?.collapsed,
              [styles.mobile]: isMobile,
            })}
          >
            <Header />
            <Content chat={chat} />
            <Footer
              status={status}
              loading={loading}
              onSubmit={onSubmit}
              onClear={onClear}
            />
          </div>
        );
      }}
    </RouteContext.Consumer>
  );
};
