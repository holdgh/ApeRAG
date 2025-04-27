import { Document } from '@/api';
import { Merge } from './tool';

export type DocumentConfig = {
  path?: string;
  labels?: {
    [key in string]: string;
  }[];
};

export type ApeDocument = Merge<
  Document,
  {
    config?: DocumentConfig;
  }
>;
