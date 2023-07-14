export type TypesDatabaseConfigDbType =
  | 'mysql'
  | 'postgresql'
  | 'sqlite'
  | 'redis'
  | 'oracle'
  | 'mongo'
  | 'clickhouse'
  | 'elasticsearch';

export type TypesDatabaseConfigCerify = 'prefered' | 'ca_only' | 'full';

export type TypesDatabaseConfigDbTypeOption = {
  label: string;
  value: TypesDatabaseConfigDbType;
  icon: string;
  showSelector?: boolean;
  disabled?: boolean;
};

export type TypesCollectionConfigModels = string  //'vicuna-13b' | 'chatglm2-6b';

export type TypesDatabaseConfig = {
  host?: string;
  model?: string;

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

export type DocumentConfigSource =
  | 'system'
  | 'local'
  | 's3'
  | 'oss'
  | 'ftp'
  | 'email';

export type TypesDocumentConfig = {
  source?: DocumentConfigSource;
  model?: TypesCollectionConfigModels;

  // local and ftp
  path?: string;

  // ftp
  host?: string;
  username?: string;
  password?: string;

  // s3 | oss
  region?: string;
  access_key_id?: string;
  secret_access_key?: string;
  bucket?: string;
  dir?: string;

  // email
  pop_server?: string;
  port?: string;
  email_address?: string;
  email_password?: string;
};

export type TypesDocumentConfigSourceOption = {
  label: string;
  value: DocumentConfigSource;
};

export type TypesCollectionStatus = 'INACTIVE' | 'ACTIVE' | 'DELETED';

export type TypesCollectionType = 'document' | 'database' | 'code';

export type TypesCollectionConfig = TypesDocumentConfig | TypesDatabaseConfig;

export type TypesCollection = {
  id?: string;
  title?: string;
  status?: TypesCollectionStatus;
  type: TypesCollectionType;
  config?: TypesCollectionConfig;
  description?: string;
  created?: string;
  updated?: string;
};
