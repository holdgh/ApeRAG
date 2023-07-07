import { defineConfig } from '@umijs/max';

export default defineConfig({
  antd: {},
  access: {},
  model: {},
  initialState: {},
  publicPath: process.env.publicPath || '/',
  outputPath: './build',
  request: {},
  layout: {},
  favicons: ['https://cdn.kubeblocks.com/img/apecloud/favicon.ico'],
  metas: [{ name: 'viewport', content: 'width=device-width,initial-scale=1' }],
  cssLoaderModules: {
    exportLocalsConvention: 'camelCase',
    localIdentName: '[path][name]__[local]--[hash:base64:5]',
  },
  alias: {},
  codeSplitting: {
    jsStrategy: 'depPerChunk',
    jsStrategyOptions: {},
  },
  define: {
    API_ENDPOINT: process.env.API_ENDPOINT || 'http://127.0.0.1:8000',
    ASSETS_ENDPOINT: process.env.ASSETS_ENDPOINT || 'http://localhost:8001',
    AUTH0_DOMAIN: process.env.AUTH0_DOMAIN || 'kubechat-dev.jp.auth0.com',
    AUTH0_CLIENT_ID: process.env.AUTH0_CLIENT_ID || '',
  },
  mock:
    process.env.DATA_MOCK === 'false' || process.env.NODE_ENV === 'production'
      ? false
      : {},
  proxy: {
    '/api': {
      target: process.env.API_ENDPOINT || 'http://127.0.0.1:8000',
      changeOrigin: true,
    },
  },
  locale: {
    default: 'en-US',
    antd: true,
  },
  routes: [
    {
      path: '/',
      redirect: '/document',
    },
    {
      name: 'Documents',
      path: '/document',
      icon: 'SnippetsOutlined',
      component: './Document',
      routes: [
        {
          path: '/document',
          component: './Document/new',
        },
        {
          path: '/document/new',
          component: './Document/new',
        },
        {
          name: 'Document',
          path: '/document/:collectionId',
          hideInMenu: true,
          hideInBreadcrumb: true,
          routes: [
            {
              name: 'Setting',
              path: '/document/:collectionId',
              component: './Document/detail',
            },
            {
              name: 'Chat',
              path: '/document/:collectionId/chat',
              component: './Chat',
            },
          ],
        },
      ],
    },
    {
      name: 'Database',
      path: '/database',
      icon: 'ConsoleSqlOutlined',
      component: './Database',
      routes: [
        {
          path: '/database',
          component: './Database/new',
        },
        {
          path: '/database/new',
          component: './Database/new',
        },
        {
          name: 'Database',
          path: '/database/:collectionId',
          hideInMenu: true,
          hideInBreadcrumb: true,
          routes: [
            {
              name: 'Setting',
              path: '/database/:collectionId',
              component: './Database/detail',
            },
            {
              name: 'Chat',
              path: '/database/:collectionId/chat',
              component: './Chat',
            },
          ],
        },
      ],
    },
    {
      name: 'Code',
      path: '/code',
      icon: 'CodeOutlined',
      component: './Code',
      routes: [
        {
          path: '/code',
          component: './Code/new',
        },
        {
          path: '/code/new',
          component: './Code/new',
        },
        {
          name: 'Code',
          path: '/code/:collectionId',
          hideInMenu: true,
          hideInBreadcrumb: true,
          routes: [
            {
              name: 'Setting',
              path: '/code/:collectionId',
              component: './Code/detail',
            },
            {
              name: 'Chat',
              path: '/code/:collectionId/chat',
              component: './Chat',
            },
          ],
        },
      ],
    },
    {
      name: 'Bot Settings',
      path: '/settings',
      icon: 'SettingFilled',
      component: './Settings',
      hideInMenu: true,
    },
  ],
  npmClient: 'yarn',
  esbuildMinifyIIFE: true,
  chainWebpack: (config) => {
    config.output.chunkFilename('[contenthash:16].js').end();
    config
      .plugin('mini-css-extract-plugin')
      .tap(() => [
        {
          chunkFilename: '[contenthash:16].css',
          ignoreOrder: true,
        },
      ])
      .end();
  },
});
