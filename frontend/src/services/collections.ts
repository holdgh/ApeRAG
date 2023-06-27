import type { Collection } from '@/models/collection';
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
  collectionId: string | number,
): Promise<{ code: string; data: Collection; message?: string }> => {
  return request(`/api/v1/collections/${collectionId}`, {
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
