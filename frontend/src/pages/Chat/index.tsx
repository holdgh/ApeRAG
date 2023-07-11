import { COLLECTION_STATUS_TAG_COLORS, SOCKET_STATUS_MAP } from '@/constants';
import { getUser } from '@/models/user';
import { UpdateCollectionChat } from '@/services/chats';
import type { TypesMessage, TypesMessageReferences } from '@/types';
import { SettingOutlined } from '@ant-design/icons';
import { Link, useModel, useParams } from '@umijs/max';
import { Button, Divider, Select, Space, Tag, Typography, theme } from 'antd';
import classNames from 'classnames';
import _ from 'lodash';
import { useEffect, useState } from 'react';
import useWebSocket from 'react-use-websocket';
import Chats from './chats';
import Footer from './footer';
import styles from './index.less';

type DbChatFormFields = { database?: string };

export default () => {
  const user = getUser();
  const { collectionId } = useParams();

  // the data stream in the loading state
  const [isTyping, setIsTyping] = useState<boolean>(false);

  // websocket url & params
  const [socketUrl, setSocketUrl] = useState<string>('');
  const [socketParams, setSocketParams] = useState<DbChatFormFields>({});

  // model data;
  const { hasDatabaseSelector, currentCollection } = useModel('collection');
  const { currentDatabases, databaseLoading } = useModel('database');
  const { currentChat, setCurrentChatHistory, setCurrentChatStatus } = useModel('chat');

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

  const showSelector = hasDatabaseSelector(currentCollection);

  const updateSocketUrl = () => {
    if (
      !currentCollection ||
      !currentChat ||
      collectionId !== currentChat?.collectionId
    )
      return;

    const protocol = API_ENDPOINT.indexOf('https') > -1 ? 'wss' : 'ws';
    const hostname = API_ENDPOINT.replace(/^(http|https):\/\//, '');
    let url = `${protocol}://${hostname}/api/v1/collections/${currentCollection.id}/chats/${currentChat.id}/connect`;

    if (currentCollection.type === 'database') {
      const query = _.map(socketParams, (value, key) => `${key}=${value}`);
      if (_.includes(currentDatabases, socketParams.database)) {
        url += `?${query.join('&')}`;
        setSocketUrl(url);
      }
    } else {
      setSocketUrl(url);
    }
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
    if (isTyping) return;
    const timestamp = new Date().getTime();
    const msg: TypesMessage = {
      type: 'message',
      role: 'human',
      data,
      timestamp,
    };
    await setCurrentChatHistory(historyMessages.concat(msg));
    sendJsonMessage(msg);
  };

  useEffect(() => {
    const params: DbChatFormFields = {};
    if (!_.isEmpty(currentDatabases)) {
      Object.assign(params, {
        database: _.first(currentDatabases),
      });
    }
    setSocketParams(params);
  }, [currentDatabases]);

  useEffect(() => {
    updateSocketUrl();
  }, [currentChat, socketParams]);

  useEffect(() => {
    if (_.isEmpty(lastJsonMessage)) return;

    let msg: TypesMessage = lastJsonMessage as TypesMessage;

    let index = historyMessages.findLastIndex((m) => m.id === msg.id);
    if (index === -1) {
      index = 0;
    }

    if (msg.type === 'finish') {
      setIsTyping(false);
      setCurrentChatStatus('finish');
    }

    // set history references when all stream has been received.
    if (msg.type === 'stop') {
      setIsTyping(false);
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
    if (_.includes(['start', 'sql', 'message', 'error'], msg.type)) {
      const message: TypesMessage = {
        ...msg,
        role: 'ai',
        _typeWriter: true,
      };
      if (msg.type === 'start') {
        setIsTyping(true);
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
    <>
      <div
        className={classNames({
          [styles.header]: true,
        })}
      >
        <Space style={{ display: 'flex', justifyContent: 'space-between' }}>
          <Space split={<Divider type="vertical" />}>
            <Typography.Title level={5} style={{ margin: 0 }}>
              {currentCollection?.title}
            </Typography.Title>
            {currentCollection?.status ? (
              <Tag
                className={styles.status}
                color={COLLECTION_STATUS_TAG_COLORS[currentCollection.status]}
              >
                {_.capitalize(currentCollection?.status)}
              </Tag>
            ) : null}
          </Space>

          <Space split={<Divider type="vertical" />}>
            {showSelector ? (
              <Select
                loading={databaseLoading}
                className={styles.selector}
                bordered={false}
                value={socketParams?.database}
                onChange={(database) =>
                  setSocketParams({ ...socketParams, database })
                }
                options={currentDatabases?.map((d) => ({
                  label: d,
                  value: d,
                }))}
              />
            ) : null}
            <Link to={`/${currentCollection?.type}/${currentCollection?.id}`}>
              <Button shape="circle" type="text" icon={<SettingOutlined />} />
            </Link>
          </Space>
        </Space>
      </div>
      <Chats
        loading={isTyping}
        status={SOCKET_STATUS_MAP[readyState]}
        onExecute={onExecute}
      />
      <div
        className={classNames({
          [styles.footer]: true,
        })}
        style={{ background: '#0A0A0A' }}
      >
        <Footer
          isTyping={isTyping}
          status={SOCKET_STATUS_MAP[readyState]}
          onSubmit={onSubmit}
          onClear={onClear}
        />
      </div>
    </>
  );
};
