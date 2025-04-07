export type TypesDocumentStatus =
  | 'PENDING'
  | 'RUNNING'
  | 'FAILED'
  | 'COMPLETE'
  | 'DELETED';

export type TypesDocumentConfig = {
  labels?: {
    key: string;
    value: string;
  }[];
};

export type TypesDocument = {
  id: string;
  collectionId: string;
  name: string;
  user: string;
  status: TypesDocumentStatus;
  size: number;
  config: TypesDocumentConfig;
  created: string;
  updated: string;
};
