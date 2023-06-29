import {
  CreateCollection,
  GetCollections,
  UpdateCollection,
} from '@/services/collections';
import { history } from '@umijs/max';
import { App } from 'antd';
import _ from 'lodash';
import { useEffect, useState } from 'react';

export type CollectionConfigDbType =
  | 'mysql'
  | 'postgresql'
  | 'sqlite'
  | 'redis'
  | 'oracle'
  | 'mongo'
  | 'clickhouse'
  | 'elasticsearch';

export type CollectionConfigCerify = 'prefered' | 'ca_only' | 'full';

export type CollectionConfigDBTypeOption = {
  label: string;
  value: CollectionConfigDbType;
  icon?: string,
};

export type CollectionConfig = {
  db_type?: CollectionConfigDbType;
  host: string;
  port?: number;
  db_name?: string;
  username?: string;
  password?: string;
  verify?: CollectionConfigCerify;
  ca_cert?: string;
  client_key?: string;
  client_cert?: string;
};

export type CollectionStatus = 'INACTIVE' | 'ACTIVE' | 'DELETED';

export type CollectionType = 'document' | 'database';

export type Collection = {
  id: number;
  title: string;
  user: string;
  status: CollectionStatus;
  type: CollectionType;
  config: CollectionConfig | string;
  description: string;
  created: string;
  updated: string;
};

export const collectionConfigDBTypeOptions: CollectionConfigDBTypeOption[] = [
  {
    label: 'MySQL',
    value: 'mysql',
    icon: 'https://cdn.kubeblocks.com/img/mysql.png',
  },
  {
    label: 'PostgreSql',
    value: 'postgresql',
    icon: 'https://cdn.kubeblocks.com/img/pg.png',
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

export const getCollectionUrl = (collection: Collection): string => {
  return `/collections/${collection.id}/${
    collection.type === 'database' ? 'setting' : 'document'
  }`;
};

export default () => {
  const [collections, setCollections] = useState<Collection[]>();
  const [currentCollection, _setCurrentCollection] = useState<Collection>();

  const { message } = App.useApp();

  const getCollections = async () => {
    const { data } = await GetCollections();
    setCollections(data);
  };

  const getCollection = (id?: string | number): Collection | undefined => {
    if (!id) return;
    return collections?.find((c) => String(c.id) === String(id));
  };

  const createColection = async (params: Collection) => {
    const { data } = await CreateCollection(params);
    if (data.id) {
      message.success('create success');
      setCollections(collections?.concat(data));
      history.push(getCollectionUrl(data));
    } else {
      message.error('create error');
    }
  };

  const updateCollection = async (
    collectionId: string | number,
    params: Collection,
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
        setCollections(items);
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

  return {
    collections,
    currentCollection,
    getCollections,
    getCollection,
    createColection,
    updateCollection,
    setCurrentCollection,
  };
};
