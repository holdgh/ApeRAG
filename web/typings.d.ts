import '@umijs/max/typings';

declare global {
  const NODE_ENV: 'development' | 'production';
  const API_ENDPOINT: string;
  const BASE_PATH: string;
  const PUBLIC_PATH: string;
  const SITE_LOGO: string;
  const SITE_TITLE: string;
}
