import {
  CreateCollectionChat,
  GetCollectionChat,
  GetCollectionChats,
} from '@/services/chats';
import {
  CreateCollection,
  GetCollectionDatabase,
  GetCollections,
  UpdateCollection,
} from '@/services/collections';
import { history } from '@umijs/max';
import { App } from 'antd';
import _ from 'lodash';
import { useEffect, useState } from 'react';
import { Chat, Message } from './chat';

export type DatabaseConfigDbType =
  | 'mysql'
  | 'postgresql'
  | 'sqlite'
  | 'redis'
  | 'oracle'
  | 'mongo'
  | 'clickhouse'
  | 'elasticsearch';

export type DatabaseExecuteMethod = 'true' | 'false';

export type DatabaseConfigCerify = 'prefered' | 'ca_only' | 'full';

export type DatabaseConfigDbTypeOption = {
  label: string;
  value: DatabaseConfigDbType;
  icon?: string;
  showSelector?: boolean;
};

export type DatabaseConfig = {
  db_type?: DatabaseConfigDbType;
  host?: string;
  port?: number;
  db_name?: string;
  username?: string;
  password?: string;
  verify?: DatabaseConfigCerify;
  ca_cert?: string;
  client_key?: string;
  client_cert?: string;
};

export type DocumentConfigSource = 'system' | 'local' | 's3' | 'oss' | 'ftp';

export type DocumentConfigSourceOption = {
  label: string;
  value: DocumentConfigSource;
};

export type DocumentConfig = {
  source?: string;
};

export type CollectionStatus = 'INACTIVE' | 'ACTIVE' | 'DELETED';

export type CollectionType = 'document' | 'database' | 'document_local';

export type Collection = {
  id: string;
  title: string;
  user: string;
  status: CollectionStatus;
  type: CollectionType;
  config: string;
  description: string;
  created: string;
  updated: string;
};

export const DATABASE_EXECUTE_OPTIONS: {
  label: string;
  value: DatabaseExecuteMethod;
}[] = [
  {
    label: 'Immediate Execute',
    value: 'true',
  },
  {
    label: 'Execute on Request',
    value: 'false',
  },
];

export const DATABASE_TYPE_OPTIONS: DatabaseConfigDbTypeOption[] = [
  {
    label: 'MySQL',
    value: 'mysql',
    icon: 'https://cdn.kubeblocks.com/img/mysql.png',
    showSelector: true,
  },
  {
    label: 'PostgreSql',
    value: 'postgresql',
    icon: 'https://cdn.kubeblocks.com/img/pg.png',
    showSelector: true,
  },
  {
    label: 'SQLite',
    value: 'sqlite',
  },
  {
    label: 'Redis',
    value: 'redis',
    icon: 'https://cdn.kubeblocks.com/img/redis.svg',
  },
  {
    label: 'Oracle',
    value: 'oracle',
  },
  {
    label: 'Mongo',
    value: 'mongo',
    icon: 'https://cdn.kubeblocks.com/img/mongodb.svg',
  },
  {
    label: 'ClickHouse',
    value: 'clickhouse',
  },
  {
    label: 'ElasticSearch',
    value: 'elasticsearch',
  },
];

export const DOCUMENT_SOURCE_OPTIONS: DocumentConfigSourceOption[] = [
  {
    label: 'Default',
    value: 'system',
  },
  {
    label: 'Local',
    value: 'local',
  },
  {
    label: 'AWS S3',
    value: 's3',
  },
  {
    label: 'Aliyun OSS',
    value: 'oss',
  },
  {
    label: 'FTP',
    value: 'ftp',
  },
];

export const hasDatabaseList = (collection?: Collection): boolean => {
  const config: DatabaseConfig = {};
  const whiteList = DATABASE_TYPE_OPTIONS.filter(
    (o) => o.showSelector === true,
  ).map((o) => o.value);

  try {
    Object.assign(config, JSON.parse(collection?.config || '{}'));
  } catch (err) {}
  const isInWhiteList =
    !!config.db_type &&
    new RegExp(`^(${whiteList.join('|')})$`).test(config.db_type);
  return collection?.type === 'database' && isInWhiteList;
};

export const getCollectionUrl = (collection: Collection): string => {
  return `/collections/${collection.id}/${
    collection.type === 'database' ? 'setting' : 'document'
  }`;
};

// export const parseCollectionConfig = (
//   collection: Collection,
// ): DocumentConfig & DatabaseConfig => {
//   const config = collection.config || '{}';
//   let result: DocumentConfig & DatabaseConfig = {};
//   try {
//     result = JSON.parse(config);
//   } catch (err) {}
//   return result;
// };

export default () => {
  const [collections, _setCollections] = useState<Collection[]>();
  const [currentCollection, _setCurrentCollection] = useState<Collection>();
  const [currentChat, _setCurrentChat] = useState<Chat>();
  const [currentDatabase, _setCurrentDatabase] = useState<string[]>();
  const { message } = App.useApp();

  const _createChat = async () => {
    if (!currentCollection) return;
    const { data } = await CreateCollectionChat(currentCollection?.id);
    _setCurrentChat(data);
  };
  const _getChat = async (id: string) => {
    if (!currentCollection) return;
    const { data } = await GetCollectionChat(currentCollection.id, id);
    _setCurrentChat(data);
  };
  const _getChats = async () => {
    if (!currentCollection) return;
    const { data } = await GetCollectionChats(currentCollection?.id);
    const item = _.first(data);
    if (item) {
      _getChat(item.id);
    } else {
      await _createChat();
    }
  };
  const _getDatabase = async () => {
    if (!currentCollection) return;
    if (hasDatabaseList(currentCollection)) {
      const { data } = await GetCollectionDatabase(currentCollection.id);
      _setCurrentDatabase(data);
    }
  };

  const setCurrentChatMessages = async (messages: Message[]) => {
    if (!currentChat) return;
    _setCurrentChat({
      ...currentChat,
      history: messages,
    });
  };

  const getCollections = async () => {
    const { data } = await GetCollections();
    _setCollections(data);
  };

  const getCollection = (id?: string): Collection | undefined => {
    if (!id) return;
    return collections?.find((c) => String(c.id) === String(id));
  };

  const createColection = async (params: Collection) => {
    const { data } = await CreateCollection(params);
    if (data.id) {
      message.success('create success');
      _setCollections(collections?.concat(data));
      history.push(getCollectionUrl(data));
    } else {
      message.error('create error');
    }
  };

  const updateCollection = async (collectionId: string, params: Collection) => {
    const { data } = await UpdateCollection(collectionId, params);
    if (data.id) {
      message.success('update success');
      const index = collections?.findIndex(
        (c) => String(c.id) === String(collectionId),
      );
      if (index !== -1 && index !== undefined && collections?.length) {
        const items = _.update(collections, index, (origin) => ({
          ...origin,
          ...data,
        }));
        _setCollections(items);
      }
    } else {
      message.error('update error');
    }
  };

  const setCurrentCollection = async (collection?: Collection) => {
    if (collection) {
      localStorage.setItem('collection', JSON.stringify(collection));
      _setCurrentCollection(collection);
    } else {
      localStorage.removeItem('collection');
      _setCurrentCollection(undefined);
    }
  };

  useEffect(() => {
    if (collections === undefined) return;
    const localCollection = localStorage.getItem('collection');
    let current: Collection | undefined;
    if (localCollection) {
      try {
        current = JSON.parse(localCollection);
      } catch (err) {}
    }
    const isExsited = !!collections.find((c) => c.id === current?.id);
    if (!isExsited) {
      current = _.first(collections);
    }
    setCurrentCollection(current);
  }, [collections]);

  useEffect(() => {
    if (currentCollection) {
      _getChats();
      _getDatabase();
    } else {
      _setCurrentChat(undefined);
    }
  }, [currentCollection]);

  return {
    collections,
    currentCollection,
    currentChat,
    currentDatabase,
    setCurrentChatMessages,
    getCollections,
    getCollection,
    createColection,
    updateCollection,
    setCurrentCollection,
  };
};
