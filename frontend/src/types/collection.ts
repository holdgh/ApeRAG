
export type TypesDatabaseConfigDbType =
  | 'mysql'
  | 'postgresql'
  | 'sqlite'
  | 'redis'
  | 'oracle'
  | 'mongo'
  | 'clickhouse'
  | 'elasticsearch';

export type TypesDatabaseExecuteMethod = 'true' | 'false';

export type TypesDatabaseConfigCerify = 'prefered' | 'ca_only' | 'full';

export type TypesDatabaseConfigDbTypeOption = {
  label: string;
  value: TypesDatabaseConfigDbType;
  icon?: string;
  showSelector?: boolean;
};

export type TypesDatabaseConfig = {
  host?: string;

  // database
  db_type?: TypesDatabaseConfigDbType;
  port?: number;
  db_name?: string;
  username?: string;
  password?: string;
  verify?: TypesDatabaseConfigCerify;
  ca_cert?: string;
  client_key?: string;
  client_cert?: string;
};

export type DocumentConfigSource = 'system' | 'local' | 's3' | 'oss' | 'ftp';

export type TypesDocumentConfig = {
  source?: DocumentConfigSource;

  // local
  path?: string;

  // s3 | oss
  region?: string;
  access_key_id?: string;
  secret_access_key?: string;
  bucket?: string;
  dir?: string;

  // ftp
  host?: string;
  username?: string;
  password?: string;
};

export type TypesDocumentConfigSourceOption = {
  label: string;
  value: DocumentConfigSource;
};

export type TypesCollectionStatus = 'INACTIVE' | 'ACTIVE' | 'DELETED';

export type TypesCollectionType = 'document' | 'database' | 'document_local';

export type TypesCollection = {
  id: string;
  title?: string;
  status?: TypesCollectionStatus;
  type: TypesCollectionType;
  config?: string;
  description?: string;
  created?: string;
  updated?: string;
};
