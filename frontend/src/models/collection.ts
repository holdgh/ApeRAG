import { GetCollections } from '@/services/collections';
import { useState } from 'react';

export type Collection = {
  id: number;
  title: string;
  status: 'INACTIVE' | 'ACTIVE' | 'DELETED';
  type: 'document' | 'multimedia' | 'database';
  description: string;
  gmt_created: string;
  gmt_updated: string;
  gmt_deleted: string;
};

export default () => {
  const [collections, setCollections] = useState<Collection[]>([]);

  const getCollections = async () => {
    const { data } = await GetCollections();
    setCollections(data);
  };

  return {
    collections,
    getCollections,
  };
};
