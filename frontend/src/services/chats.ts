import type { Chat } from '@/models/chat';
import { request } from '@umijs/max';

export const GetCollectionChats = (
  collectionId: number | string,
): Promise<{ code: string; data: Chat[]; message?: string }> => {
  return request(`/api/v1/collections/${collectionId}/chats`, {
    method: 'get',
  });
};

export const GetCollectionChat = (
  collectionId: number | string,
  chatId: number | string,
): Promise<{ code: string; data: Chat[]; message?: string }> => {
  return request(`/api/v1/collections/${collectionId}/chats/${chatId}`, {
    method: 'get',
  });
};

export const CreateCollectionChat = (
  collectionId: number | string,
  data?: Chat,
): Promise<{ code: string; data: Chat; message?: string }> => {
  return request(`/api/v1/collections/${collectionId}/chats`, {
    method: 'post',
    data,
  });
};

export const DeleteCollectionChat = (
  collectionId: number | string,
  chatId: number | string,
): Promise<{ code: string; data: string | number; message?: string }> => {
  return request(`/api/v1/collections/${collectionId}/chats/${chatId}`, {
    method: 'delete',
  });
};
