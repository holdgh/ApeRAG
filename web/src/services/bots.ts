import { TypesBot } from '@/types';
import { request } from '@umijs/max';

export const GetBots = (): Promise<{
  code: string;
  data: TypesBot[];
  message?: string;
}> => {
  return request(`/api/v1/bots`, {
    method: 'GET',
  });
};

export const GetBot = (
  botId: string,
): Promise<{ code: string; data: TypesBot; message?: string }> => {
  return request(`/api/v1/bots/${botId}`, {
    method: 'GET',
  });
};

export const ListIntegraions = (
  botId: string,
): Promise<{ code: string; data: TypesBot; message?: string }> => {
  return request(`/api/v1/bots/${botId}/integrations`, {
    method: 'GET',
  });
};

export const CreateBot = (
  data: TypesBot,
): Promise<{
  code: string;
  data: TypesBot;
  message?: string;
}> => {
  return request(`/api/v1/bots`, {
    method: 'POST',
    data,
  });
};

export const UpdateBot = (
  botId: string,
  data: TypesBot,
): Promise<{ code: string; data: TypesBot; message?: string }> => {
  return request(`/api/v1/bots/${botId}`, {
    method: 'PUT',
    data,
  });
};

export const DeleteBot = (
  botId: string,
): Promise<{ code: string; data: string; message?: string }> => {
  return request(`/api/v1/bots/${botId}`, {
    method: 'DELETE',
  });
};
