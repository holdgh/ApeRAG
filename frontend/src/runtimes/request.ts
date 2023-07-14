import { getUser } from '@/models/user';
import type { RequestConfig } from '@umijs/max';

export const request: RequestConfig = {
  requestInterceptors: [
    async (options: any) => {
      const user = getUser();
      if (user) {
        options.headers['Authorization'] = 'Bearer ' + user.__raw;
      }
      if (!options.url.match(/^http/)) {
        options.url = `${API_ENDPOINT}${options.url}`;
      }
      return options;
    },
  ],
  responseInterceptors: [
    (response) => {
      return response;
    },
  ],
};
