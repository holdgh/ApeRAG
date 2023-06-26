import { GetCollections } from '@/services/collections';
import { useEffect, useState } from 'react';

export type Collection = {
  id: number;
  title: string;
  status: 'Active' | 'InActive';
  type: 'Document' | 'Multimedia';
  description: string;
};

export default () => {
  const [collections, setCollections] = useState<Collection[]>([]);

  const getCollections = async () => {
    const { data } = await GetCollections();
    setCollections(data);
  };

  useEffect(() => {
    getCollections();
  }, []);

  return {
    collections,
  };
};
