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
  codeSplitting: {
    jsStrategy: 'depPerChunk',
    jsStrategyOptions: {},
  },
  define: {
    ASSETS_ENDPOINT: process.env.ASSETS_ENDPOINT || 'http://localhost:8001',
    AUTH0_DOMAIN: process.env.AUTH0_DOMAIN || '',
    AUTH0_CLIENT_ID: process.env.AUTH0_CLIENT_ID || '',
  },
  mock:
    process.env.DATA_MOCK === 'false' || process.env.NODE_ENV === 'production'
      ? false
      : {},
  proxy: {
    '/api': {
      target: process.env.API_ENDPOINT || 'http://localhost:8000',
      changeOrigin: true,
    },
  },
  routes: [
    {
      path: '/',
      redirect: '/chat',
    },
    {
      name: 'Chat',
      path: '/chat',
      icon: 'MessageOutlined',
      component: './Chat',
    },
    {
      name: 'Collections',
      path: '/collections',
      icon: 'UnorderedListOutlined',
      routes: [
        {
          path: '/collections',
          component: './Collections',
        },
        {
          name: 'New Collection',
          path: '/collections/new',
          component: './Collections/new',
          hideInMenu: true,
          hideInBreadcrumb: true,
        },
        {
          name: 'Documents',
          path: '/collections/:collectionId',
          component: './Documents',
          hideInMenu: true,
          hideInBreadcrumb: true,
          routes: [
            {
              name: 'Documents',
              path: '/collections/:collectionId/documents',
              component: './Documents/list',
            },
            {
              name: 'Setting',
              path: '/collections/:collectionId/setting',
              component: './Collections/edit',
            },
          ],
        },
      ],
    },
    {
      name: 'Bot Settings',
      path: '/settings',
      icon: 'SettingOutlined',
      component: './Settings',
    },
  ],
  npmClient: 'yarn',
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
