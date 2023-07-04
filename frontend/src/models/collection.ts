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

import type {
  TypesChat,
  TypesCollection,
  TypesCollectionStatus,
  TypesDatabaseConfig,
  TypesDatabaseConfigDbTypeOption,
  TypesDatabaseExecuteMethod,
  TypesDocumentConfig,
  TypesDocumentConfigSourceOption,
  TypesDocumentStatus,
  TypesMessage,
  TypesSocketStatus,
} from '@/types';
import { PresetStatusColorType } from 'antd/es/_util/colors';
import { ReadyState } from 'react-use-websocket';

export const DATABASE_DEFAULT_CONFIG: TypesCollection = {
  type: 'database',
  config: '', // default is empty.
};
export const DOCUMENT_DEFAULT_CONFIG: TypesCollection = {
  type: 'document',
  config: '{"source": "system"}',
};

export const DATABASE_EXECUTE_OPTIONS: {
  label: string;
  value: TypesDatabaseExecuteMethod;
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

export const DATABASE_TYPE_OPTIONS: TypesDatabaseConfigDbTypeOption[] = [
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

export const DOCUMENT_SOURCE_OPTIONS: TypesDocumentConfigSourceOption[] = [
  {
    label: 'System',
    value: 'system',
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
  {
    label: 'Email',
    value: 'email',
  },
];

if (process.env.NODE_ENV === 'development') {
  DOCUMENT_SOURCE_OPTIONS.splice(1, 0, {
    label: 'Local',
    value: 'local',
  });
}

export const COLLECTION_STATUS_TAG_COLORS: {
  [key in TypesCollectionStatus]: PresetStatusColorType;
} = {
  INACTIVE: 'error',
  ACTIVE: 'success',
  DELETED: 'error',
};

export const DOCUMENT_STATUS_TAG_COLORS: {
  [key in TypesDocumentStatus]: PresetStatusColorType;
} = {
  PENDING: 'warning',
  RUNNING: 'processing',
  FAILED: 'error',
  COMPLETE: 'success',
  DELETED: 'default',
};

export const SOCKET_STATUS_MAP: { [key in ReadyState]: TypesSocketStatus } = {
  [ReadyState.CONNECTING]: 'Connecting',
  [ReadyState.OPEN]: 'Open',
  [ReadyState.CLOSING]: 'Closing',
  [ReadyState.CLOSED]: 'Closed',
  [ReadyState.UNINSTANTIATED]: 'Uninstantiated',
};

export default () => {
  const [collections, _setCollections] = useState<TypesCollection[]>();
  const [currentCollection, _setCurrentCollection] =
    useState<TypesCollection>();
  const [currentChat, _setCurrentChat] = useState<TypesChat>();
  const [currentDatabase, _setCurrentDatabase] = useState<string[]>();
  const { message } = App.useApp();

  const hasDatabaseSelector = (collection?: TypesCollection): boolean => {
    const config: TypesDatabaseConfig = {};
    const whiteList = DATABASE_TYPE_OPTIONS.filter(
      (o) => o.showSelector === true,
    ).map((o) => o.value);

    try {
      Object.assign(config, JSON.parse(collection?.config || '{}'));
    } catch (err) {}
    const isInWhiteList =
      !!config.db_type &&
      new RegExp(`^(${whiteList.join('|')})$`).test(config.db_type);
    return isInWhiteList;
  };

  const getCollectionUrl = (collection: TypesCollection): string => {
    return `/collections/${collection.id}/${
      collection.type === 'database' ? 'setting' : 'document'
    }`;
  };

  const parseCollectionConfig = (
    collection?: TypesCollection,
  ): TypesDocumentConfig & TypesDatabaseConfig => {
    if (!collection) return {};

    const config = collection.config || '{}';
    let result: TypesDocumentConfig & TypesDatabaseConfig = {};
    try {
      result = JSON.parse(config);
    } catch (err) {}
    return result;
  };

  const _createChat = async () => {
    if (!currentCollection?.id) return;
    const { data } = await CreateCollectionChat(currentCollection.id);
    _setCurrentChat(data);
  };
  const _getChat = async (id: string) => {
    if (!currentCollection?.id) return;
    const { data } = await GetCollectionChat(currentCollection.id, id);
    _setCurrentChat(data);
  };
  const _getChats = async () => {
    if (!currentCollection?.id) return;
    const { data } = await GetCollectionChats(currentCollection.id);
    const item = _.first(data);
    if (item) {
      _getChat(item.id);
    } else {
      await _createChat();
    }
  };

  const _getDatabase = async () => {
    if (!currentCollection?.id) return;
    if (hasDatabaseSelector(currentCollection)) {
      const { data } = await GetCollectionDatabase(currentCollection.id);
      _setCurrentDatabase(data || []);
    }
  };

  const setCurrentChatHistory = async (data: TypesMessage[]) => {
    if (!currentChat) return;
    _setCurrentChat({
      ...currentChat,
      history: data,
    });
  };

  const getCollections = async () => {
    const { data } = await GetCollections();
    _setCollections(data);
  };

  const getCollection = (id?: string): TypesCollection | undefined => {
    if (!id) return;
    return collections?.find((c) => String(c.id) === String(id));
  };

  const createColection = async (params: TypesCollection) => {
    const { data } = await CreateCollection(params);
    if (data.id) {
      message.success('create success');
      _setCollections(collections?.concat(data));
      history.push(getCollectionUrl(data));
    } else {
      message.error('create error');
    }
  };

  const updateCollection = async (
    collectionId: string,
    params: TypesCollection,
  ) => {
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

  const setCurrentCollection = async (collection?: TypesCollection) => {
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
    let current: TypesCollection | undefined;
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
    hasDatabaseSelector,
    getCollectionUrl,
    parseCollectionConfig,

    setCurrentChatHistory,
    getCollections,
    getCollection,
    createColection,
    updateCollection,
    setCurrentCollection,
  };
};
