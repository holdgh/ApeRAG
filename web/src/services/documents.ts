import type { TypesDocument } from '@/types';
import { request } from '@umijs/max';

export const GetCollectionDocuments = (
  collectionId: string,
  pageNumber: number,
  pageSize: number,
): Promise<{ code: string; data: TypesDocument[]; message?: string }> => {
  return request(
    `/api/v1/collections/${collectionId}/documents`,{
      method: 'GET',
      params: {
        page_size: pageSize,
        page_number: pageNumber||1,
        order_by: 'gmt_updated',
        order_desc: true,
      },
    }
  );
};

export const createCollectionUrls = (
  collectionId: string,
  data: { url: string }[],
): Promise<{ code: string; data: TypesDocument[]; message?: string }> => {
  return request(`/api/v1/collections/${collectionId}/urls`, {
    method: 'post',
    data,
  });
};

export const UpdateDocument = (
  collectionId: string,
  documentId: string,
  data: TypesDocument,
): Promise<{ code: string; data: TypesDocument; message?: string }> => {
  return request(
    `/api/v1/collections/${collectionId}/documents/${documentId}`,
    {
      method: 'PUT',
      data,
    },
  );
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

export const DeleteCollectionDocuments = (
  collectionId: string,
  data:{document_ids: string}[],
): Promise<{ code: string; data: string; message?: string }> => {
  return request(
    `/api/v1/collections/${collectionId}/documents`,
    {
      method: 'delete',
      data,
    },
  );
};