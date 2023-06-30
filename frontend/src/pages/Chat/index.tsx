import type { Message, SocketStatus, Chat } from '@/models/chat';
import type { Collection } from '@/models/collection';
import { getUser } from '@/models/user';
import { UpdateCollectionChat } from '@/services/chats';
import { RouteContext, RouteContextType } from '@ant-design/pro-components';
import { useModel } from '@umijs/max';
import classNames from 'classnames';
import _ from 'lodash';
import { useEffect, useState } from 'react';
import useWebSocket, { ReadyState } from 'react-use-websocket';
import Content from './content';
import Footer from './footer';
import Header from './header';
import styles from './index.less';

const SocketStatusMap: { [key in ReadyState]: SocketStatus } = {
  [ReadyState.CONNECTING]: 'Connecting',
  [ReadyState.OPEN]: 'Open',
  [ReadyState.CLOSING]: 'Closing',
  [ReadyState.CLOSED]: 'Closed',
  [ReadyState.UNINSTANTIATED]: 'Uninstantiated',
};

const getSocketUrl = (collection?: Collection, chat?: Chat) => {
  const protocol = API_ENDPOINT.indexOf('https') > -1 ? 'wss' : 'ws';
  const hostname = API_ENDPOINT.replace(/^(http|https):\/\//, '');
  const url = `${protocol}://${hostname}/api/v1/collections/${collection?.id}/chats/${chat?.id}/connect`;
  return url;
}

export default () => {
  const user = getUser();
  const { currentCollection, currentChat, setCurrentChatMessages } =
    useModel('collection');
  const [loading, setLoading] = useState<boolean>(false);
  const [socketUrl, setSocketUrl] = useState<string>(getSocketUrl(currentCollection, currentChat));
  const { initialState } = useModel('@@initialState');
  
  const { sendMessage, lastMessage, readyState } = useWebSocket(socketUrl, {
    share: true,
    protocols: user?.__raw,
    shouldReconnect: () => true,
    reconnectInterval: 5000,
  });
  const messages = currentChat?.history || [];

  const onClear = async () => {
    if (!currentCollection || !currentChat) return;
    const { data } = await UpdateCollectionChat(
      currentCollection.id,
      currentChat.id,
      {
        ...currentChat,
        history: [],
      },
    );
    if (data.id) setCurrentChatMessages([]);
  };

  const onSubmit = async (data: string) => {
    const timestamp = new Date().getTime();
    const msg: Message = {
      type: 'message',
      role: 'human',
      data,
      timestamp,
    };
    await setCurrentChatMessages(messages.concat(msg));
    await setLoading(true);
    sendMessage(JSON.stringify(msg));
  };

  useEffect(() => {
    setLoading(SocketStatusMap[readyState] !== 'Open');
  }, [readyState])

  useEffect(() => {
    setSocketUrl(getSocketUrl(currentCollection, currentChat));
  }, [currentCollection, currentChat]);

  useEffect(() => {
    if (!lastMessage) return;
    let msg: Message = {};
    try {
      msg = JSON.parse(lastMessage.data);
    } catch (err) {}

    if (msg.type === 'error') {
      return;
    }

    if (msg.type === 'stop') {
      setLoading(false);
      return;
    }

    if (msg.type === 'message' && msg.data) {
      const message: Message = { ...msg, role: 'ai' };
      const data = _.cloneDeep(messages);
      let isAiLast = _.last(data)?.role !== 'human';
      if (isAiLast && loading) {
        _.update(data, data.length - 1, (origin) => ({
          ...message,
          data: (origin?.data || '') + msg.data,
        }));
      } else {
        data.push(message);
      }
      setCurrentChatMessages(data);
    }
  }, [lastMessage]);

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
            <Content loading={loading} messages={messages} />
            <Footer
              status={SocketStatusMap[readyState]}
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
