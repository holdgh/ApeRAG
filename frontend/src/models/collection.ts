import { Collection, Document } from '@/api';
import { api } from '@/services';
import { CollectionConfig, DocumentConfig } from '@/types';
import { parseConfig, stringifyConfig } from '@/utils';
import { useCallback, useState } from 'react';
import { useModel } from 'umi';

export default () => {
  const { setLoading } = useModel('global');

  const [collection, setCollection] = useState<Collection>();
  const [collectionLoading, setCollectionLoading] = useState<boolean>(false);

  const [collections, setCollections] = useState<Collection[]>();
  const [collectionsLoading, setCollectionsLoading] = useState<boolean>(false);

  const [documents, setDocuments] = useState<Document[]>();
  const [documentsLoading, setDocumentsLoading] = useState(false);

  // collection
  const getCollection = useCallback(async (collectionId: string) => {
    setLoading(true);
    setCollectionLoading(true);

    const res = await api.collectionsCollectionIdGet({ collectionId });
    if (typeof res.data?.config === 'string') {
      res.data.config = parseConfig(res.data.config) as CollectionConfig;
    }
    setCollection(res.data);
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
    async (data: Collection): Promise<boolean | undefined> => {
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
          config: parseConfig(res.data?.config as string),
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
    res.data.items?.forEach((item) => {
      if (typeof item.config === 'string') {
        item.config = parseConfig(item.config) as CollectionConfig;
      }
    });
    setLoading(false);
    setCollectionsLoading(false);
    setCollections(res.data.items);
  }, []);

  // collection documents
  const getDocuments = useCallback(async (collectionId: string) => {
    setLoading(true);
    setDocumentsLoading(true);
    const res = await api.collectionsCollectionIdDocumentsGet({ collectionId });
    res?.data.items?.forEach((document) => {
      if (typeof document.config === 'string') {
        document.config = parseConfig(document.config) as DocumentConfig;
      }
    });
    setLoading(false);
    setDocuments(res.data.items);
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
