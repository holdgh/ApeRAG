import type { Collection } from './collection';

export type DocumentStatus =
  | 'PENDING'
  | 'RUNNING'
  | 'FAILED'
  | 'COMPLETE'
  | 'DELETED';

export type Document = {
  id: string;
  name: string;
  user: string;
  collection: Collection;
  status: DocumentStatus;
  size: number;
  created: string;
  updated: string;
};

export default () => {};
