import { Config } from '@/api';
import 'umi/typings';

declare global {
  const APERAG_CONFIG: {
    title?: string;
    favicon?: string;
    logo_dark?: string;
    logo_light?: string;
    github?: string;
  } & Config;

  const BASE_PATH: string;
  const PUBLIC_PATH: string;
}
