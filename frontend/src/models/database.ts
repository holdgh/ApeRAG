import { GetCollectionDatabase } from '@/services/collections';
import { useModel } from '@umijs/max';
import { App } from 'antd';
import _ from 'lodash';
import { useEffect, useState } from 'react';

export default () => {
  const [databases, setDatabases] = useState<{ [key in string]: string[] }>({});
  const [databaseLoading, setDatabaseLoading] = useState<boolean>(false);
  const { currentCollection, hasDatabaseSelector, getCollection } =
    useModel('collection');

  const { message } = App.useApp();

  const getCollectionDatabases = async (collectionId?: string) => {
    if (!collectionId || !hasDatabaseSelector(getCollection(collectionId))) {
      return;
    }

    const currentCollectionDatabases = databases[collectionId];
    if (_.isEmpty(currentCollectionDatabases)) {
      setDatabaseLoading(true);
      const res = await GetCollectionDatabase(collectionId);
      if (res.code !== '200') {
        message.error(res.message || "can't connect database.");
      } else {
        _.set(databases, collectionId, res.data);
        setDatabases(databases);
      }
      setDatabaseLoading(false);
    } else {
    }
  };

  useEffect(() => {
    if (currentCollection) {
      getCollectionDatabases(currentCollection.id);
    }
  }, [currentCollection]);

  return {
    databases,
    databaseLoading,
  };
};
