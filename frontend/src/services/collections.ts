import type { Collection, CollectionConfig } from '@/models/collection';
import { request } from '@umijs/max';

export const GetCollections = (): Promise<{
  code: string;
  data: Collection[];
  message?: string;
}> => {
  return request(`/api/v1/collections`, {
    method: 'GET',
  });
};

export const ReadCollection = (
  collectionId: string,
): Promise<{ code: string; data: Collection; message?: string }> => {
  return request(`/api/v1/collections/${collectionId}`, {
    method: 'GET',
  });
};

export const GetCollectionDatabase = (
  collectionId: string,
): Promise<{ code: string; data: string[]; message?: string }> => {
  return request(`/api/v1/collections/${collectionId}/database`, {
    method: 'GET',
  });
};

export const CreateCollection = (
  data: Collection,
): Promise<{ code: string; data: Collection; message?: string }> => {
  return request(`/api/v1/collections`, {
    method: 'POST',
    data,
  });
};

export const TestCollection = (config: CollectionConfig): Promise<{ code: string; data: boolean; message?: string }> => {
  return request(`/api/v1/collections/test_connection`, {
    method: 'POST',
    data: config
  });
};

export const UpdateCollection = (
  collectionId: string | number,
  data: Collection,
): Promise<{ code: string; data: Collection; message?: string }> => {
  return request(`/api/v1/collections/${collectionId}`, {
    method: 'PUT',
    data,
  });
};

export const DeleteCollection = (
  collectionId: string | number,
): Promise<{ code: string; data: string | number; message?: string }> => {
  return request(`/api/v1/collections/${collectionId}`, {
    method: 'DELETE',
  });
};
