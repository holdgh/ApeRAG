import {
  DATABASE_EXECUTE_OPTIONS,
  hasDatabaseSelector,
} from '@/models/collection';
import { getUser } from '@/models/user';
import { UpdateCollectionChat } from '@/services/chats';
import type {
  TypesMessage,
  TypesMessageReferences,
  TypesSocketStatus,
} from '@/types';
import { RouteContext, RouteContextType } from '@ant-design/pro-components';
import { useModel } from '@umijs/max';
import { App, Form, Radio, Select, Space } from 'antd';
import classNames from 'classnames';
import _ from 'lodash';
import { useEffect, useState } from 'react';
import useWebSocket, { ReadyState } from 'react-use-websocket';
import Chats from './chats';
import Footer from './footer';
import Header from './header';
import styles from './index.less';

const SocketStatusMap: { [key in ReadyState]: TypesSocketStatus } = {
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
  const [socketParams, setSocketParams] = useState<DbChatFormFields>();
  const { initialState } = useModel('@@initialState');
  const {
    currentCollection,
    currentChat,
    currentDatabase,
    setCurrentChatMessages,
  } = useModel('collection');
  const { message } = App.useApp();

  const user = getUser();
  const messages = currentChat?.history || [];

  const { sendMessage, lastMessage, readyState } = useWebSocket(socketUrl, {
    share: true,
    protocols: user?.__raw,
    shouldReconnect: () => true,
    reconnectInterval: 5000,
    reconnectAttempts: 5,
  });
  const [paramsForm] = Form.useForm();

  const showSelector = hasDatabaseSelector(currentCollection);

  const updateSocketUrl = () => {
    if (!currentCollection || !currentChat) return;

    const protocol = API_ENDPOINT.indexOf('https') > -1 ? 'wss' : 'ws';
    const hostname = API_ENDPOINT.replace(/^(http|https):\/\//, '');
    let url = `${protocol}://${hostname}/api/v1/collections/${currentCollection.id}/chats/${currentChat.id}/connect`;

    if (currentCollection.type === 'database') {
      const query = _.map(socketParams, (value, key) => `${key}=${value}`);
      if (!_.isEmpty(query)) {
        url += `?${query.join('&')}`;
      }
    }

    setSocketUrl(url);
  };

  const onExecuteSQL = async (msg?: TypesMessage) => {
    if (msg?.type === 'sql') {
      await setCurrentChatMessages(
        messages.concat({
          type: 'message',
          role: 'ai',
          data: '',
        }),
      );
      await setLoading(true);
      sendMessage(JSON.stringify(msg));
    }
  };

  const onClear = async () => {
    if (!currentCollection?.id || !currentChat?.id) return;
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
    if (loading) return;
    const timestamp = new Date().getTime();
    const msg: TypesMessage = {
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
    if (currentDatabase) {
      const values = {
        database: _.first(currentDatabase),
        execute: _.last(DATABASE_EXECUTE_OPTIONS)?.value,
      };
      setSocketParams(values);
      paramsForm.setFieldsValue(values);
    }
  }, [currentDatabase]);

  useEffect(() => {
    updateSocketUrl();
  }, [currentCollection, currentChat]);

  useEffect(() => {
    if (!_.isEmpty(socketParams)) {
      updateSocketUrl();
    }
  }, [socketParams]);

  useEffect(() => {
    if (!lastMessage) return;
    let msg: TypesMessage = {};
    try {
      msg = JSON.parse(lastMessage.data);
    } catch (err) {}

    if (msg.type === 'error') {
      if (msg.data) message.error(msg.data);
      return;
    }

    if (msg.type === 'stop') {
      setLoading(false);
      if (_.last(messages)?.role === 'ai') {
        const references: TypesMessageReferences[] =
          msg.data as unknown as TypesMessageReferences[];
        if (msg.data) {
          _.update(messages, messages.length - 1, (origin) => ({
            ...origin,
            references,
          }));
          setCurrentChatMessages(messages);
        }
      }

      return;
    }

    if (_.includes(['sql', 'message'], msg.type) && msg.data) {
      const message: TypesMessage = { ...msg, role: 'ai' };
      let isAiLast = _.last(messages)?.role !== 'human';

      if (isAiLast && loading) {
        _.update(messages, messages.length - 1, (origin) => ({
          ...message,
          data: (origin?.data || '') + msg.data,
        }));
      } else {
        messages.push(message);
      }
      setCurrentChatMessages(messages);
    }
  }, [lastMessage]);

  const DatabaseSelector = (
    <Space>
      <Form
        form={paramsForm}
        layout="inline"
        onValuesChange={(changedValues, allValues) =>
          setSocketParams(allValues)
        }
      >
        {showSelector ? (
          <Form.Item name="database">
            <Select
              style={{ width: 140 }}
              options={currentDatabase?.map((d) => ({ label: d, value: d }))}
            />
          </Form.Item>
        ) : null}
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
            <Header
              extra={
                currentCollection?.type === 'database' ? DatabaseSelector : null
              }
            />
            <Chats
              loading={loading}
              onExecuteSQL={onExecuteSQL}
              status={SocketStatusMap[readyState]}
            />
            <Footer loading={loading} onSubmit={onSubmit} onClear={onClear} />
          </div>
        );
      }}
    </RouteContext.Consumer>
  );
};
