import { getUser } from '@/models/user';
import { RequestConfig, getLocale } from '@umijs/max';
import { message } from 'antd';

export const request: RequestConfig = {
  errorConfig: {
    errorHandler: (e) => {
      message.open({
        type: 'error',
        content: (<>
          {e.response.data&&e.response.data.code?e.response.data.code:e.message}<br/>
          {e.response.data&&e.response.data.message?JSON.stringify(e.response.data.message):'On featch '+e.config?.url}
          </>
        ),
        className: 'error-msg',
      });
    },
  },
  requestInterceptors: [
    async (options: any) => {
      const user = getUser();
      const lang = getLocale();
      if (user) {
        options.headers['Authorization'] = 'Bearer ' + user.__raw;
      }
      options.headers['lang'] = lang;
      return options;
    },
  ],
  responseInterceptors: [
    (response) => {
      const { status, data } = response as any;
      const code = data?.code;
      const msg = data?.message;

      if (status === 200) {
        if (code && code !== '200' && message) {
          message.open({
            type: 'error',
            content: msg,
            className: 'error-msg',
          });
        }
      }
      return response;
    },
  ],
};
