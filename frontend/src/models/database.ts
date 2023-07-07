import { GetCollectionDatabase } from '@/services/collections';
import { useModel } from '@umijs/max';
import { App } from 'antd';
import _ from 'lodash';
import { useEffect, useState } from 'react';

export default () => {
  const [databases, setDatabases] = useState<{ [key in string]: string[] }>({});
  const [currentDatabase, setCurrentDatabase] = useState<string[]>();
  const [databaseLoading, setDatabaseLoading] = useState<boolean>(false);
  const { currentCollection, hasDatabaseSelector } = useModel('collection');

  const { message } = App.useApp();

  const getDatabase = async () => {
    if (!currentCollection?.id || !hasDatabaseSelector(currentCollection)) {
      return;
    }

    if(_.isEmpty(databases[currentCollection.id])) {
      setDatabaseLoading(true);
      setCurrentDatabase(undefined);
      const res = await GetCollectionDatabase(currentCollection.id);
      if (res.code !== '200') {
        message.error(res.message || "can't connect database.");
      } else {
        setCurrentDatabase(res.data || []);
  
        _.set(databases, currentCollection.id, res.data || []);
        setDatabases(databases);
  
        setDatabaseLoading(false);
      }
    } else {
      setCurrentDatabase(databases[currentCollection.id]);
    }
    
  };

  useEffect(() => {
    getDatabase();
  }, [currentCollection]);

  return {
    databaseLoading,
    currentDatabase,
  };
};
