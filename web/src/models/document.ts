import {
  GetCollectionDocuments,
  DeleteCollectionDocument,
  DeleteCollectionDocuments,
} from '@/services/documents';
import type { TypesDocument } from '@/types';
import { parseConfig } from '@/utils/configParse';
import { useState } from 'react';


export default () => {
  const [documents, setDocuments] = useState<TypesDocument[]>();
  const [documentLoading, setDocumentLoading] = useState<boolean>(false);
  const [totalCount, setTotalCount] = useState<number>(0);

  const getDocuments = async (collectionId, pagenumber, pagesize) => {
    setDocumentLoading(true);
    const { count, data } = await GetCollectionDocuments(String(collectionId), pagenumber, pagesize);

    data.forEach((d) => {
      d.config = parseConfig(d.config as unknown as string);
    });

    // data.sort(
    //   (a, b) => new Date(b.updated).getTime() - new Date(a.updated).getTime(),
    // );

    setDocuments(data);
    setDocumentLoading(false);
    setTotalCount(count);
  };

  const deleteDocument = async (collectionId, documentId) => {
    if (!collectionId || !documentId) return;
    let code = '';
    if(_.isArray(documentId)){
      let { code } = await DeleteCollectionDocuments(collectionId, documentId);
    }else{
      let { code } = await DeleteCollectionDocument(collectionId, documentId);
    }
    if (code === '200') {
      return true;
    }
  };

  return {
    documents,
    documentLoading,
    totalCount,
    getDocuments,
    deleteDocument
  };
};
