import { api } from '@/services';
import { ApeCollection, ApeDocument } from '@/types';
import { parseConfig, stringifyConfig } from '@/utils';
import { useCallback, useState } from 'react';
import { useModel } from 'umi';

export default () => {
  const { setLoading } = useModel('global');

  const [collection, setCollection] = useState<ApeCollection>();
  const [collectionLoading, setCollectionLoading] = useState<boolean>(false);

  const [collections, setCollections] = useState<ApeCollection[]>();
  const [collectionsLoading, setCollectionsLoading] = useState<boolean>(false);

  const [documents, setDocuments] = useState<ApeDocument[]>();
  const [documentsLoading, setDocumentsLoading] = useState(false);

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

  // collection documents
  const getDocuments = useCallback(async (collectionId: string) => {
    setLoading(true);
    setDocumentsLoading(true);
    const res = await api.collectionsCollectionIdDocumentsGet({ collectionId });

    setLoading(false);
    setDocuments(
      res.data.items?.map((document) => ({
        ...document,
        config: parseConfig(document.config),
      })),
    );

    setDocumentsLoading(false);
  }, []);

  // document
  const deleteDocument = useCallback(
    async (documentId: string): Promise<boolean | undefined> => {
      if (!collection?.id) return;
      setLoading(true);
      const res = await api.collectionsCollectionIdDocumentsDocumentIdDelete({
        collectionId: collection.id,
        documentId,
      });
      getDocuments(collection.id);
      setLoading(false);
      return res.status === 200;
    },
    [collection],
  );

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

    documents,
    documentsLoading,
    getDocuments,
    setDocuments,

    deleteDocument,
  };
};
