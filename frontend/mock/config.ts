export default {
  'GET /api/v1/config': {
    code: '200',
    data: {
      auth: {
        type: 'cookie', // auth0 | authing | logto | none | cookie
        auth_domain: 'kubechat.jp.auth0.com',
        auth_app_id: 'G6RuQZZNaDorHGUEOv7Mgq1COqfryTB2',
      },
      public_ips: [],
    },
  },
};
