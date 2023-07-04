import { GetCollectionDatabase } from '@/services/collections';
import { useModel } from '@umijs/max';
import { useEffect, useState } from 'react';

export default () => {
  const [currentDatabase, setCurrentDatabase] = useState<string[]>();
  const [databaseLoading, setDatabaseLoading] = useState<boolean>(false);
  const { currentCollection, hasDatabaseSelector } = useModel('collection');

  const getDatabase = async () => {
    if (!currentCollection?.id) return;
    if (hasDatabaseSelector(currentCollection)) {
      setDatabaseLoading(true);
      const { data } = await GetCollectionDatabase(currentCollection.id);
      setCurrentDatabase(data || []);
      setDatabaseLoading(false);
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
