import type { TypesDocument } from '@/models/document';
import { request } from '@umijs/max';

export const GetCollectionDocuments = (
  collectionId: number | string,
): Promise<{ code: string; data: TypesDocument[]; message?: string }> => {
  return request(`/api/v1/collections/${collectionId}/documents`);
};

export const DeleteCollectionDocument = (
  collectionId: number | string,
  documentId: number,
): Promise<{ code: string; data: string | number; message?: string }> => {
  return request(
    `/api/v1/collections/${collectionId}/documents/${documentId}`,
    {
      method: 'delete',
    },
  );
};
