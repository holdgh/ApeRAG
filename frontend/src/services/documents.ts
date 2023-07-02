import type { TypesDocument } from '@/types';
import { request } from '@umijs/max';

export const GetCollectionDocuments = (
  collectionId: string,
): Promise<{ code: string; data: TypesDocument[]; message?: string }> => {
  return request(`/api/v1/collections/${collectionId}/documents`);
};

export const DeleteCollectionDocument = (
  collectionId: string,
  documentId: string,
): Promise<{ code: string; data: string; message?: string }> => {
  return request(
    `/api/v1/collections/${collectionId}/documents/${documentId}`,
    {
      method: 'delete',
    },
  );
};
