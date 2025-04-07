import type { TypesCollection, TypesCollectionSyncHistory } from '@/types';
import { request } from '@umijs/max';

export const GetCollections = (
  pageNumber: number,
  pageSize: number,
): Promise<{
  code: string;
  data: TypesCollection[];
  message?: string;
}> => {
  return request(`/api/v1/collections`, {
    method: 'GET',
    params: {
      page_size: pageSize,
      page_number: pageNumber||1,
      order_by: 'gmt_updated',
      order_desc: true,
    },
  });
};

export const GetDefaultCollections = (
  pageNumber: number,
  pageSize: number,
): Promise<{
  code: string;
  data: TypesCollection[];
  message?: string;
}> => {
  return request(`/api/v1/default_collections`, {
    method: 'GET',
    params: {
      page_size: pageSize,
      page_number: pageNumber||1,
      order_by: 'gmt_updated',
      order_desc: true,
    },
  });
};

export const GetRelatedQuestions = (
  collectionId: string,
  pageNumber: number,
  pageSize: number,
): Promise<{ code: string; data: TypesCollection; message?: string }> => {
  return request(`/api/v1/collections/${collectionId}/questions`, {
    method: 'GET',
    params: {
      page_size: pageSize,
      page_number: pageNumber||1,
    },
  });
};

export const GenRelatedQuestions = (
  collectionId: string,
): Promise<{ code: string; data: TypesCollection; message?: string }> => {
  return request(`/api/v1/collections/${collectionId}/questions`, {
    method: 'POST',
  });
};

export const DeleteRelatedQuestion = (
  collectionId: string,
  questionId: string,
): Promise<{ code: string; data: TypesCollection; message?: string }> => {
  return request(`/api/v1/collections/${collectionId}/questions/${questionId}`, {
    method: 'DELETE',
  });
};

export const UpdateRelatedQuestion = (
  collectionId: string,
  data: any,
): Promise<{ code: string; data: TypesCollection; message?: string }> => {
  return request(`/api/v1/collections/${collectionId}/questions`, {
    method: 'PUT',
    data,
  });
};

export const GetQuestionDetails = (
  collectionId: string,
  questionId: number,
): Promise<{ code: string; data: TypesCollection; message?: string }> => {
  return request(`/api/v1/collections/${collectionId}/questions/${questionId}`, {
    method: 'GET',
  });
};

export const ReadCollection = (
  collectionId: string,
): Promise<{ code: string; data: TypesCollection; message?: string }> => {
  return request(`/api/v1/collections/${collectionId}`, {
    method: 'GET',
  });
};

export const CreateCollection = (
  data: TypesCollection,
): Promise<{ code: string; data: TypesCollection; message?: string }> => {
  return request(`/api/v1/collections`, {
    method: 'POST',
    data,
  });
};

export const UpdateCollection = (
  collectionId: string,
  data: TypesCollection,
): Promise<{ code: string; data: TypesCollection; message?: string }> => {
  return request(`/api/v1/collections/${collectionId}`, {
    method: 'PUT',
    data,
  });
};

export const DeleteCollection = (
  collectionId: string,
): Promise<{ code: string; data: string; message?: string }> => {
  return request(`/api/v1/collections/${collectionId}`, {
    method: 'DELETE',
  });
};

export const GetCollectionSyncHistories = (
  collectionId: string,
): Promise<{ code: string; data: TypesCollectionSyncHistory[] }> => {
  return request(`/api/v1/collections/${collectionId}/sync/history`, {
    method: 'GET',
    params:{
      order_by: 'gmt_created',
      order_desc: true,
    },
  });
};

export const GetCollectionSyncHistory = (
  collectionId: string,
  syncId: string,
): Promise<{ code: string; data: TypesCollectionSyncHistory }> => {
  return request(`/api/v1/collections/${collectionId}/sync/${syncId}`, {
    method: 'GET',
  });
};

export const SyncCollection = (
  collectionId: string,
): Promise<{
  code: string;
  data: TypesCollectionSyncHistory;
  message?: string;
}> => {
  return request(`/api/v1/collections/${collectionId}/sync`, {
    method: 'POST',
  });
};

export const CancelSyncCollection = (
  collectionId: string,
  collectionSyncId: string,
): Promise<{ code: string; data: TypesCollectionSyncHistory }> => {
  return request(
    `/api/v1/collections/${collectionId}/cancel_sync/${collectionSyncId}`,
    {
      method: 'POST',
    },
  );
};
