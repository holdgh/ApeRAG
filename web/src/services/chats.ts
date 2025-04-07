import type { TypesChat, TypesMessage } from '@/types';
import { request } from '@umijs/max';

export const GetChats = (
  botId: string,
): Promise<{ code: string; data: TypesChat[]; message?: string }> => {
  return request(`/api/v1/bots/${botId}/chats`, {
    method: 'get',
  });
};

export const GetChat = (
  botId: string,
  chatId: string,
): Promise<{ code: string; data: TypesChat; message?: string }> => {
  return request(`/api/v1/bots/${botId}/chats/${chatId}`, {
    method: 'get',
  });
};

export const CreateChat = (
  botId: string,
  data?: TypesChat,
): Promise<{ code: string; data: TypesChat; message?: string }> => {
  return request(`/api/v1/bots/${botId}/chats`, {
    method: 'post',
    data,
  });
};

export const UpdateChat = (
  botId: string,
  chatId: string,
  data?: TypesChat,
): Promise<{ code: string; data: TypesChat; message?: string }> => {
  return request(`/api/v1/bots/${botId}/chats/${chatId}`, {
    method: 'put',
    data,
  });
};

export const DeleteChat = (
  botId: string,
  chatId: string,
): Promise<{ code: string; data: string; message?: string }> => {
  return request(`/api/v1/bots/${botId}/chats/${chatId}`, {
    method: 'delete',
  });
};

export const VoteChatMessage = (
  botId: string,
  chatId: string,
  messageId: string,
  data: TypesMessage,
): Promise<{ code: string; data: string; message?: string }> => {
  return request(
    `/api/v1/bots/${botId}/chats/${chatId}/messages/${messageId}`,
    {
      method: 'post',
      data,
    },
  );
};
