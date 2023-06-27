import { Chat } from '@/models/chat';
import { CreateCollectionChat, GetCollectionChats } from '@/services/chats';
import { useModel } from '@umijs/max';
import { Button, Input, Space, Tooltip, Typography, theme } from 'antd';
import _ from 'lodash';
import { useEffect, useState } from 'react';
// import { useEffect } from 'react';

import CollectionTitle from '@/components/CollectionTitle';
import { ClearOutlined, SendOutlined } from '@ant-design/icons';
import classNames from 'classnames';
import styles from './index.less';
import Item from './item';

export default () => {
  const [chat, setChat] = useState<Chat | undefined>();
  const { currentCollection } = useModel('collection');
  const { initialState } = useModel('@@initialState');

  const { token } = theme.useToken();

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
      <div
        className={styles.header}
        style={{ borderBottom: `1px solid ${token.colorBorderSecondary}` }}
      >
        <CollectionTitle collection={chat?.collection} />
      </div>
      <div className={styles.content}>
        {chat?.history.map((item, key) => (
          <Item key={key} />
        ))}
      </div>
      <div
        className={styles.footer}
        style={{ borderTop: `1px solid ${token.colorBorderSecondary}` }}
      >
        <Input
          suffix={
            <Space>
              <Tooltip title="Clear">
                <Button
                  type="text"
                  icon={
                    <Typography.Text type="secondary">
                      <ClearOutlined />
                    </Typography.Text>
                  }
                ></Button>
              </Tooltip>
              <Tooltip title="Send">
                <Button
                  type="text"
                  icon={
                    <Typography.Text style={{ color: token.colorPrimary }}>
                      <SendOutlined />
                    </Typography.Text>
                  }
                ></Button>
              </Tooltip>
            </Space>
          }
          autoFocus
          size="large"
          bordered={false}
          placeholder="Enter your question here..."
        />
      </div>
    </div>
  );
};
