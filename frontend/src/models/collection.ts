import { GetCollections, ReadCollection } from '@/services/collections';
import _ from 'lodash';
import { useEffect, useState } from 'react';
import { getUser } from './user';

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
  const user = getUser();

  const getCollections = async (
    force: boolean | undefined = true,
  ): Promise<Collection[] | undefined> => {
    if (force || !collections?.length) {
      const { data } = await GetCollections();
      setCollections(data);
      return data;
    } else {
      return collections;
    }
  };

  const getCollection = async (
    id: string | number,
    force: boolean | undefined = true,
  ): Promise<Collection | undefined> => {
    if (force) {
      const data = await getCollections();
      return data?.find((c) => String(c.id) === String(id));
    } else {
      const { data } = await ReadCollection(id);
      return data;
    }
  };

  const setCurrentCollection = (collection?: Collection) => {
    if (collection) {
      localStorage.setItem('collection', JSON.stringify(collection));
      _setCurrentCollection(collection);
    } else {
      localStorage.removeItem('collection');
      _setCurrentCollection(undefined);
    }
  };

  useEffect(() => {
    const localCollection = localStorage.getItem('collection');
    let current: Collection | undefined;
    if (localCollection) {
      try {
        current = JSON.parse(localCollection);
      } catch (err) {}
    }
    const isExsited = !!collections?.find((c) => c.id === current?.id);
    if (!isExsited) {
      current = _.first(collections);
    }
    setCurrentCollection(current);
  }, [collections]);

  return {
    collections,

    getCollections,
    getCollection,

    currentCollection,
    setCurrentCollection,
  };
};
