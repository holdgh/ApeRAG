import type { Collection } from './collection';

export type Document = {
  id: number;
  name: string;
  user: string;
  collection: Collection;
  status: 'RUNNING' | 'COMPLETE' | 'FAILED' | 'DELETED' | 'PENDING';
  size: number;
  created: string;
  updated: string;
};

export default () => {};
