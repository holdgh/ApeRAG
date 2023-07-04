import CollectionTitle from '@/components/CollectionTitle';
import {
  DATABASE_EXECUTE_OPTIONS,
  SOCKET_STATUS_MAP,
} from '@/models/collection';
import { getUser } from '@/models/user';
import { UpdateCollectionChat } from '@/services/chats';
import type { TypesMessage, TypesMessageReferences } from '@/types';
import { RouteContext, RouteContextType } from '@ant-design/pro-components';
import { useModel } from '@umijs/max';
import { Form, Radio, Select, Space, Tag, theme } from 'antd';
import classNames from 'classnames';
import _ from 'lodash';
import { useEffect, useState } from 'react';
import useWebSocket from 'react-use-websocket';
import Chats from './chats';
import Footer from './footer';
import styles from './index.less';

type DbChatFormFields = { [key in string]: string | undefined };

export default () => {
  // const { message } = App.useApp();

  // the data stream in the loading state
  const [loading, setLoading] = useState<boolean>(false);

  // websocket url
  const [socketUrl, setSocketUrl] = useState<string>('');

  // websocket params
  const [socketParams, setSocketParams] = useState<DbChatFormFields>();

  const { hasDatabaseSelector } = useModel('collection');

  // initialState.collapsed for mobile adaptation;
  const { initialState } = useModel('@@initialState');

  // login user;
  const user = getUser();

  // theme tokens;
  const { token } = theme.useToken();

  // collection model data;
  const {
    currentCollection,
    currentChat,
    currentDatabase,
    setCurrentChatHistory,
  } = useModel('collection');

  // history list;
  const historyMessages = currentChat?.history || [];

  // web socket instance
  const { sendJsonMessage, lastJsonMessage, readyState } = useWebSocket(
    socketUrl,
    {
      share: true,
      protocols: user?.__raw,
      shouldReconnect: () => true,
      reconnectInterval: 5000,
      reconnectAttempts: 5,
    },
  );

  // db form instance;
  const [dbSelectorForm] = Form.useForm();

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

  const onExecute = async (msg: TypesMessage) => {
    sendJsonMessage(msg);
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
    if (data.id) setCurrentChatHistory([]);
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
    await setCurrentChatHistory(historyMessages.concat(msg));
    await setLoading(true);
    sendJsonMessage(msg);
  };

  useEffect(() => {
    if (!_.isEmpty(currentDatabase)) {
      const values = {
        database: _.first(currentDatabase),
        execute: _.last(DATABASE_EXECUTE_OPTIONS)?.value,
      };
      setSocketParams(values);
    } else {
      setSocketParams({});
    }
  }, [currentDatabase]);

  useEffect(() => {
    updateSocketUrl();
  }, [currentCollection, currentChat]);

  useEffect(() => {
    if (!_.isEmpty(socketParams)) {
      dbSelectorForm.setFieldsValue(socketParams);
      updateSocketUrl();
    }
  }, [socketParams]);

  useEffect(() => {
    if (SOCKET_STATUS_MAP[readyState] !== 'Open') {
      setLoading(false);
    }
  }, [readyState]);

  useEffect(() => {
    if (_.isEmpty(lastJsonMessage)) return;

    let msg: TypesMessage = lastJsonMessage as TypesMessage;

    let index = historyMessages.findLastIndex((m) => m.id === msg.id);
    if (index === -1) {
      index = 0;
    }

    // message stream is error.
    if (msg.type === 'error') {
      setLoading(false);
    }

    // set history references when all stream has been received.
    if (msg.type === 'stop') {
      setLoading(false);
      const references = msg.data as unknown as TypesMessageReferences[];
      if (msg.data) {
        _.update(historyMessages, index, (origin) => ({
          ...origin,
          references,
        }));
        setCurrentChatHistory(historyMessages);
      }
    }

    // create a new message or update a old message.
    if (_.includes(['start', 'sql', 'message'], msg.type)) {
      const message: TypesMessage = {
        ...msg,
        role: 'ai',
        _typeWriter: true,
      };
      if (msg.type === 'start') {
        setLoading(true);
        historyMessages.push(message);
      } else {
        _.update(historyMessages, index, (origin) => ({
          ...message,
          data: (origin?.data || '') + msg.data, // append new stream data
        }));
      }
      setCurrentChatHistory(historyMessages);
    }
  }, [lastJsonMessage]);

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
            <div
              className={styles.header}
              style={{
                borderBottom: `1px solid ${token.colorBorderSecondary}`,
              }}
            >
              <Space
                style={{ display: 'flex', justifyContent: 'space-between' }}
                align="center"
              >
                <Space>
                  <CollectionTitle collection={currentCollection} />
                  <Tag
                    color={
                      currentCollection?.status === 'ACTIVE'
                        ? 'success'
                        : 'error'
                    }
                  >
                    {_.capitalize(currentCollection?.status)}
                  </Tag>
                </Space>
                {currentCollection?.type === 'database' ? (
                  <Space>
                    <Form
                      form={dbSelectorForm}
                      layout="inline"
                      onValuesChange={(changedValues, allValues) =>
                        setSocketParams(allValues)
                      }
                    >
                      {showSelector ? (
                        <Form.Item name="database">
                          <Select
                            style={{ width: 140 }}
                            options={currentDatabase?.map((d) => ({
                              label: d,
                              value: d,
                            }))}
                          />
                        </Form.Item>
                      ) : null}
                      <Form.Item name="execute">
                        <Radio.Group options={DATABASE_EXECUTE_OPTIONS} />
                      </Form.Item>
                    </Form>
                  </Space>
                ) : null}
              </Space>
            </div>
            <Chats
              loading={loading}
              status={SOCKET_STATUS_MAP[readyState]}
              onExecute={onExecute}
            />
            <Footer
              status={SOCKET_STATUS_MAP[readyState]}
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
