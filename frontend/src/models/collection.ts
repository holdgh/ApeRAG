import { DATABASE_TYPE_OPTIONS } from '@/constants';
import {
  CreateCollection,
  GetCollections,
  UpdateCollection,
} from '@/services/collections';
import type {
  TypesCollection,
  TypesDatabaseConfig,
  TypesDocumentConfig,
} from '@/types';
import { history } from '@umijs/max';
import { App } from 'antd';
import _ from 'lodash';
import { useEffect, useState } from 'react';

export default () => {
  const [collections, setCollections] = useState<TypesCollection[]>();
  const [currentCollection, setCurrentCollection] = useState<TypesCollection>();
  const [collectionLoading, setCollectionLoading] = useState<boolean>(false);
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

  const getCollections = async () => {
    setCollectionLoading(true);
    const { data } = await GetCollections();
    setCollectionLoading(false);

    setCollections(data);
  };

  const getCollection = (id?: string): TypesCollection | undefined => {
    if (!id) return;
    return collections?.find((c) => String(c.id) === String(id));
  };

  const createColection = async (params: TypesCollection) => {
    setCollectionLoading(true);
    const { data } = await CreateCollection(params);
    setCollectionLoading(false);

    if (data.id) {
      message.success('create success');
      setCollections(collections?.concat(data));
      history.push(getCollectionUrl(data));
    } else {
      message.error('create error');
    }
  };

  const updateCollection = async (
    collectionId: string,
    params: TypesCollection,
  ) => {
    setCollectionLoading(true);
    const { data } = await UpdateCollection(collectionId, params);
    setCollectionLoading(false);

    if (data.id) {
      message.success('update success');
      const index = collections?.findIndex(
        (c) => String(c.id) === String(collectionId),
      );
      if (index !== -1 && collections?.length && index !== undefined) {
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

  useEffect(() => {
    if (collections === undefined) return;
    const localCollectionString = localStorage.getItem('collection');
    let localCollection: TypesCollection | undefined = undefined;
    if (localCollectionString) {
      try {
        localCollection = JSON.parse(localCollectionString);
      } catch (err) {}
    }

    const item = collections.find((c) => c.id === localCollection?.id);
    if (localCollection?.id === item?.id) {
      setCurrentCollection(item);
    } else {
      setCurrentCollection(undefined);
      localStorage.removeItem('collection');
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
    getCollectionUrl,
    parseCollectionConfig,

    getCollections,
    getCollection,
    createColection,
    updateCollection,
    setCurrentCollection,
  };
};
