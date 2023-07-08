import { GetCollectionDatabase } from '@/services/collections';
import { useModel } from '@umijs/max';
import { App } from 'antd';
import _ from 'lodash';
import { useEffect, useState } from 'react';

export default () => {
  const [databases, setDatabases] = useState<{ [key in string]: string[] }>({});
  const [currentDatabases, setCurrentDatabases] = useState<string[]>();
  const [databaseLoading, setDatabaseLoading] = useState<boolean>(false);
  const { currentCollection, hasDatabaseSelector } = useModel('collection');

  const { message } = App.useApp();

  const getCollectionDatabases = async () => {
    setCurrentDatabases(undefined);

    if (!currentCollection?.id || !hasDatabaseSelector(currentCollection)) {
      return;
    }

    const currentCollectionDatabases = databases[currentCollection.id];
    if(_.isEmpty(currentCollectionDatabases)) {
      setDatabaseLoading(true);
      const res = await GetCollectionDatabase(currentCollection.id);
      if (res.code !== '200') {
        message.error(res.message || "can't connect database.");
      } else {
        setCurrentDatabases(res.data);
        _.set(databases, currentCollection.id, res.data);
        setDatabases(databases);
      }
      setDatabaseLoading(false);
    } else {
      setCurrentDatabases(currentCollectionDatabases);
    }
    
  };

  useEffect(() => {
    getCollectionDatabases();
  }, [currentCollection]);

  return {
    databaseLoading,
    currentDatabases,
  };
};
