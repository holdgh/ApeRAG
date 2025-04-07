import { TypesModels } from '@/types';
import { request } from '@umijs/max';

export const GetModels = (): Promise<{ code: string; data: TypesModels[] }> => {
  return request(`/api/v1/models`, {
    method: 'GET',
  });
};

export const GetChractors = (): Promise<{ code: string; data: any }> => {
  return request(`/api/v1/prompt_templates`, {
    method: 'GET',
  });
};