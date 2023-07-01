import type { TypesChat } from '@/types';
import { request } from '@umijs/max';

export const GetCollectionChats = (
  collectionId: string,
): Promise<{ code: string; data: TypesChat[]; message?: string }> => {
  return request(`/api/v1/collections/${collectionId}/chats`, {
    method: 'get',
  });
};

export const GetCollectionChat = (
  collectionId: string,
  chatId: string,
): Promise<{ code: string; data: TypesChat; message?: string }> => {
  return request(`/api/v1/collections/${collectionId}/chats/${chatId}`, {
    method: 'get',
  });
};

export const CreateCollectionChat = (
  collectionId: string,
  data?: TypesChat,
): Promise<{ code: string; data: TypesChat; message?: string }> => {
  return request(`/api/v1/collections/${collectionId}/chats`, {
    method: 'post',
    data,
  });
};

export const UpdateCollectionChat = (
  collectionId: string,
  chatId: string,
  data?: TypesChat,
): Promise<{ code: string; data: TypesChat; message?: string }> => {
  return request(`/api/v1/collections/${collectionId}/chats/${chatId}`, {
    method: 'put',
    data,
  });
};

export const DeleteCollectionChat = (
  collectionId: string,
  chatId: string,
): Promise<{ code: string; data: string; message?: string }> => {
  return request(`/api/v1/collections/${collectionId}/chats/${chatId}`, {
    method: 'delete',
  });
};
