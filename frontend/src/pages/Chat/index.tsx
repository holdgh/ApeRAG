import type { Message, SocketStatus } from '@/models/chat';
import { DATABASE_EXECUTE_OPTIONS, hasDatabaseList } from '@/models/collection';
import { getUser } from '@/models/user';
import { UpdateCollectionChat } from '@/services/chats';
import { RouteContext, RouteContextType } from '@ant-design/pro-components';
import { useModel } from '@umijs/max';
import { Form, Radio, Select, Space } from 'antd';
import classNames from 'classnames';
import _ from 'lodash';
import { useEffect, useState } from 'react';
import useWebSocket, { ReadyState } from 'react-use-websocket';
import Chats from './chats';
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

type DbChatFormFields = { [key in string]: string | undefined };

export default () => {
  const [loading, setLoading] = useState<boolean>(false);
  const [socketUrl, setSocketUrl] = useState<string>('');
  const { initialState } = useModel('@@initialState');
  const {
    currentCollection,
    currentChat,
    currentDatabase,
    setCurrentChatMessages,
  } = useModel('collection');
  const user = getUser();
  const { sendMessage, lastMessage, readyState } = useWebSocket(socketUrl, {
    share: true,
    protocols: user?.__raw,
    shouldReconnect: () => true,
    reconnectInterval: 5000,
    reconnectAttempts: 5,
  });
  const [dbForm] = Form.useForm();

  const messages = currentChat?.history || [];
  const showSelector = hasDatabaseList(currentCollection);

  const defaultDbChatFormValue: DbChatFormFields = {
    database: _.first(currentDatabase),
    execute: _.first(DATABASE_EXECUTE_OPTIONS)?.value,
  };
  const updateSocketUrl = (params?: DbChatFormFields) => {
    if (!currentCollection || !currentChat) return;

    const protocol = API_ENDPOINT.indexOf('https') > -1 ? 'wss' : 'ws';
    const hostname = API_ENDPOINT.replace(/^(http|https):\/\//, '');
    let url = `${protocol}://${hostname}/api/v1/collections/${currentCollection.id}/chats/${currentChat.id}/connect`;

    if (showSelector) {
      if (_.isEmpty(currentDatabase)) return;

      const query = _.map(
        { ...defaultDbChatFormValue, ...params },
        (value, key) => `${key}=${value}`,
      );
      if (!_.isEmpty(query)) url += `?${query.join('&')}`;
    }

    setSocketUrl(url);
  };

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
  }, [readyState]);

  useEffect(() => {
    updateSocketUrl();
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

  const DatabaseSelector = (
    <Space>
      <Form
        form={dbForm}
        layout="inline"
        onValuesChange={(changedValues, allValues) => {
          updateSocketUrl(allValues);
        }}
        initialValues={defaultDbChatFormValue}
      >
        <Form.Item name="database">
          <Select
            style={{ width: 140 }}
            options={currentDatabase?.map((d) => ({ label: d, value: d }))}
          />
        </Form.Item>
        <Form.Item name="execute">
          <Radio.Group options={DATABASE_EXECUTE_OPTIONS} />
        </Form.Item>
      </Form>
    </Space>
  );

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
            <Header extra={showSelector ? DatabaseSelector : null} />
            <Chats
              status={SocketStatusMap[readyState]}
              loading={loading}
              messages={messages}
            />
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
