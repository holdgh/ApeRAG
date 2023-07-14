import type { TypesCollection, TypesDatabaseConfig } from '@/types';
import { request } from '@umijs/max';

export const GetCollections = (): Promise<{
  code: string;
  data: TypesCollection[];
  message?: string;
}> => {
  return request(`/api/v1/collections`, {
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

export const GetCollectionDatabase = (
  collectionId: string,
): Promise<{ code: string; data: string[]; message?: string }> => {
  return request(`/api/v1/collections/${collectionId}/database`, {
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

export const TestCollection = (
  config: TypesDatabaseConfig,
): Promise<{ code: string; data: boolean; message?: string }> => {
  return request(`/api/v1/collections/test_connection`, {
    method: 'POST',
    data: config,
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

export const CodeDownload = (chatId: string) => {
  return request(`/api/v1/code/codegenerate/download/${chatId}`, {
    method: 'GET',
    responseType: 'blob'
  });
};

export const GetModels = (): Promise<{ code: string, data: string[] }> => {
  return request(`/api/v1/collections/model_name`, {
    method: 'GET',
  });
};
