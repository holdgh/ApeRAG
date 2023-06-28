import type { Collection } from './collection';

export type Document = {
  id: number;
  name: string;
  user: string;
  collection: Collection;
  status: 'PENDING' | 'RUNNING' | 'FAILED' | 'COMPLETE' | 'DELETED';
  size: number;
  created: string;
  updated: string;
};

export default () => {};
