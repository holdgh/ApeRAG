export type TypesDocumentStatus =
  | 'PENDING'
  | 'RUNNING'
  | 'FAILED'
  | 'COMPLETE'
  | 'DELETED';

export type TypesDocument = {
  id: string;
  collectionId: string;
  name: string;
  user: string;
  status: TypesDocumentStatus;
  size: number;
  created: string;
  updated: string;
};
