import { CreateCollection, GetCollections, UpdateCollection } from '@/services/collections';
import _ from 'lodash';
import { useEffect, useState } from 'react';
import { history } from '@umijs/max';
import { App } from 'antd';

export type Collection = {
  id: number;
  title: string;
  user: string;
  status: 'INACTIVE' | 'ACTIVE' | 'DELETED';
  type: 'document' | 'multimedia' | 'database';
  config: string;
  description: string;
  gmt_created: string;
  gmt_updated: string;
  gmt_deleted: string;
};

export default () => {
  const [collections, setCollections] = useState<Collection[]>();
  const [currentCollection, _setCurrentCollection] = useState<Collection>();

  const { message } = App.useApp();

  const getCollections = async () => {
    const { data } = await GetCollections();
    setCollections(data);
  };

  const getCollection = (
    id?: string | number,
  ): Collection | undefined => {
    if(!id) return;
    return collections?.find((c) => String(c.id) === String(id));
  };

  const createColection = async (params: Collection) => {
    const { data } = await CreateCollection(params);
    if (data.id) {
      message.success('create success');
      setCollections(collections?.concat(data));
      history.push(`/collections/${data.id}/documents`);
    } else {
      message.error('create error');
    }
  }

  const updateCollection = async (collectionId: string | number, params: Collection) => {
    const { data } = await UpdateCollection(collectionId, params);
    if (data.id) {
      message.success('update success');
      const index = collections?.findIndex(c => String(c.id) === String(collectionId));
      if(index !== -1 && index !== undefined && collections?.length) {
        const items = _.update(collections, index, (origin) => ({ ...origin, ...data}));
        setCollections(items);
      }
    } else {
      message.error('update error');
    }
  }

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
    if(collections === undefined) return;

    const localCollection = localStorage.getItem('collection');
    let current: Collection | undefined;
    if (localCollection) {
      try {
        current = JSON.parse(localCollection);
      } catch (err) {}
    }
    const isExsited = collections!== undefined && collections.find((c) => c.id === current?.id);
    if (!isExsited) {
      current = _.first(collections);
    }
    setCurrentCollection(current);
  }, [collections]);

  return {
    collections,

    getCollections,
    getCollection,

    createColection,
    updateCollection,

    currentCollection,
    setCurrentCollection,
  };
};
