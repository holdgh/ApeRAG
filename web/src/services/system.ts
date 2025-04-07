import { SystemConfig } from '@/types';
import { request } from '@umijs/max';

export const GetSystemConfig = (): Promise<{
  code: string;
  data?: SystemConfig;
}> => {
  return request(`/api/v1/config`);
};
