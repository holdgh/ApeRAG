import { getUser } from '@/models/user';
import type { RequestConfig } from '@umijs/max';

export const request: RequestConfig = {
  requestInterceptors: [
    async (options: any) => {
      const user = getUser();
      if (user) {
        options.headers['Authorization'] = 'Bearer ' + user.__raw;
      }
      return options;
    },
  ],
};
