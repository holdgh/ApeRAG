import { GetSystemConfig } from '@/services';
import { SystemConfig } from '@/types';

export let env: SystemConfig;

export const initializeSystem = async () => {
  const res = await GetSystemConfig();

  env = res.data

  // env.auth = {
  //   type: 'none',
  // }
};
