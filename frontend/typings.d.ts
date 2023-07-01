import '@umijs/max/typings';

import '@/types';

declare global {
  const API_ENDPOINT: string;
  const ASSETS_ENDPOINT: string;
  const AUTH0_CLIENT_ID: string;
  const AUTH0_DOMAIN: string;
}
