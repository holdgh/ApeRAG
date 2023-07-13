import { DATABASE_TYPE_OPTIONS } from '@/constants';
import {
  CreateCollection,
  DeleteCollection,
  GetCollections,
  UpdateCollection,
} from '@/services/collections';
import type {
  TypesCollection,
  TypesCollectionConfig,
  TypesDatabaseConfig,
} from '@/types';
import { history } from '@umijs/max';
import { App } from 'antd';
import _ from 'lodash';
import { useEffect, useState } from 'react';

const parseConfig = (configString: string) => {
  const config = {};
  try {
    Object.assign(config, JSON.parse(configString));
  } catch (err) {}
  return config;
};

const stringifyConfig = (config?: TypesCollectionConfig): string => {
  let configString = '{}';
  try {
    configString = JSON.stringify(config);
  } catch (err) {}
  return configString;
};

export default () => {
  const [collections, setCollections] = useState<TypesCollection[]>();
  const [currentCollection, setCurrentCollection] = useState<TypesCollection>();
  const [collectionLoading, setCollectionLoading] = useState<boolean>(false);
  const { message } = App.useApp();

  const hasDatabaseSelector = (collection?: TypesCollection): boolean => {
    if (collection?.type !== 'database') return false;
    const config = collection?.config as TypesDatabaseConfig;

    const whiteList = DATABASE_TYPE_OPTIONS.filter(
      (o) => o.showSelector === true,
    ).map((o) => o.value);

    const isInWhiteList =
      !!config?.db_type &&
      new RegExp(`^(${whiteList.join('|')})$`).test(config.db_type);
    return isInWhiteList;
  };

  const getCollections = async () => {
    setCollectionLoading(true);
    const { data } = await GetCollections();

    data.forEach((d) => {
      d.config = parseConfig(d.config as string);
    });

    setCollectionLoading(false);

    setCollections(data);
  };

  const getCollection = (id?: string): TypesCollection | undefined => {
    if (!id) return;
    return collections?.find((c) => String(c.id) === String(id));
  };

  const deleteCollection = async (collection?: TypesCollection) => {
    if (!collections || !collection?.id) return;
    const { code } = await DeleteCollection(collection.id);
    if (code === '200') {
      setCollections(collections.filter((c) => c.id !== collection.id));
      setTimeout(() => {
        history.push(`/${collection.type}`);
      });
    } else {
      message.error('delete error');
    }
  };

  const getLocalCollection = (): TypesCollection | undefined => {
    const localCollectionString = localStorage.getItem('collection');
    let localCollection: TypesCollection | undefined = undefined;
    if (localCollectionString) {
      try {
        localCollection = JSON.parse(localCollectionString);
      } catch (err) {}
    }
    return localCollection;
  };

  const createColection = async (params: TypesCollection) => {
    setCollectionLoading(true);

    params.config = stringifyConfig(params.config) as TypesCollectionConfig;
    const { data } = await CreateCollection(params);
    data.config = parseConfig(data.config as string);

    setCollectionLoading(false);

    if (data.id) {
      message.success('create success');
      setCollections(collections?.concat(data));
      history.push(`/${data.type}/${data.id}`);
    } else {
      message.error('create error');
    }
  };

  const updateCollection = async (
    collectionId: string,
    params: TypesCollection,
  ) => {
    setCollectionLoading(true);

    params.config = stringifyConfig(params.config) as TypesCollectionConfig;
    const { data } = await UpdateCollection(collectionId, params);
    data.config = parseConfig(data.config as string);

    setCollectionLoading(false);

    if (data.id) {
      message.success('update success');
      const index = collections?.findIndex((c) => c.id === collectionId);
      if (index !== -1 && collections?.length && index !== undefined) {
        _.update(collections, index, (origin) => ({
          ...origin,
          ...data,
        }));
        setCollections(collections);
      }
    } else {
      message.error('update error');
    }
  };

  useEffect(() => {
    const localCollection = getLocalCollection();
    const item = collections?.find((c) => c.id === localCollection?.id);

    if (item) {
      setCurrentCollection(item);
    } else {
      const current = _.first(collections);
      if (current) {
        setCurrentCollection(current);
      } else {
        setCurrentCollection(undefined);
        localStorage.removeItem('collection');
      }
    }
  }, [collections]);

  useEffect(() => {
    if (currentCollection) {
      localStorage.setItem('collection', JSON.stringify(currentCollection));
    }
  }, [currentCollection]);

  return {
    collections,
    currentCollection,
    collectionLoading,

    hasDatabaseSelector,

    getCollections,
    getCollection,
    deleteCollection,
    getLocalCollection,
    createColection,
    updateCollection,
    setCurrentCollection,
  };
};
