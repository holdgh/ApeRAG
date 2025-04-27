import { api } from '@/services';
import { ApeCollection } from '@/types';
import { parseConfig, stringifyConfig } from '@/utils';
import { useCallback, useState } from 'react';
import { useModel } from 'umi';

export default () => {
  const { setLoading } = useModel('global');

  const [collection, setCollection] = useState<ApeCollection>();
  const [collectionLoading, setCollectionLoading] = useState<boolean>(false);

  const [collections, setCollections] = useState<ApeCollection[]>();
  const [collectionsLoading, setCollectionsLoading] = useState<boolean>(false);

  // collection
  const getCollection = useCallback(async (collectionId: string) => {
    setLoading(true);
    setCollectionLoading(true);
    const res = await api.collectionsCollectionIdGet({ collectionId });
    setCollection({
      ...res.data,
      config: parseConfig(res.data.config),
    });
    setLoading(false);
    setCollectionLoading(false);
  }, []);

  const deleteCollection = useCallback(
    async (collectionId: string): Promise<boolean | undefined> => {
      const res = await api.collectionsCollectionIdDelete({ collectionId });
      return res.status === 200;
    },
    [],
  );

  const updateCollection = useCallback(
    async (data: ApeCollection): Promise<boolean | undefined> => {
      if (!data.id) return;
      const config = stringifyConfig(data.config) as string;
      const res = await api.collectionsCollectionIdPut({
        collectionId: data.id,
        collectionUpdate: { ...data, config },
      });
      const success = res.status === 200;
      if (success) {
        setCollection({
          ...res.data,
          config: parseConfig(res.data?.config),
        });
      }
      return success;
    },
    [],
  );

  // collections
  const getCollections = useCallback(async () => {
    setLoading(true);
    setCollectionsLoading(true);
    const res = await api.collectionsGet();

    setLoading(false);
    setCollectionsLoading(false);
    setCollections(
      res.data.items?.map((item) => ({
        ...item,
        config: parseConfig(item.config),
      })),
    );
  }, []);

  return {
    collection,
    collectionLoading,
    getCollection,
    setCollection,

    deleteCollection,
    updateCollection,

    collections,
    collectionsLoading,
    getCollections,
    setCollections,
  };
};
