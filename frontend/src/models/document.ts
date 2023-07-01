import type { TypesCollection } from './collection';

export type TypesDocumentStatus =
  | 'PENDING'
  | 'RUNNING'
  | 'FAILED'
  | 'COMPLETE'
  | 'DELETED';

export type TypesDocument = {
  id: string;
  name: string;
  user: string;
  collection: TypesCollection;
  status: TypesDocumentStatus;
  size: number;
  created: string;
  updated: string;
};

export default () => {};
