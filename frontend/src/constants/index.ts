import { TypesCollection, TypesCollectionStatus, TypesDatabaseConfigDbTypeOption, TypesDatabaseExecuteMethod, TypesDocumentConfigSourceOption, TypesDocumentStatus, TypesSocketStatus } from "@/types";
import { PresetStatusColorType } from "antd/es/_util/colors";
import { ReadyState } from "react-use-websocket";

export const DOCUMENT_DEFAULT_CONFIG: TypesCollection = {
  type: 'document',
  config: '{"source": "system"}',
};

export const CODE_DEFAULT_CONFIG: TypesCollection = {
  type: 'code',
  config: '{}',
};

export const DATABASE_DEFAULT_CONFIG: TypesCollection = {
  type: 'database',
  config: '', // default is empty.
};

export const DATABASE_EXECUTE_OPTIONS: {
  label: string;
  value: TypesDatabaseExecuteMethod;
}[] = [
  {
    label: 'Immediate Execute',
    value: 'true',
  },
  {
    label: 'Execute on Request',
    value: 'false',
  },
];

export const DATABASE_TYPE_OPTIONS: TypesDatabaseConfigDbTypeOption[] = [
  {
    label: 'MySQL',
    value: 'mysql',
    icon: 'https://cdn.kubeblocks.com/img/mysql.png',
    showSelector: true,
  },
  {
    label: 'PostgreSql',
    value: 'postgresql',
    icon: 'https://cdn.kubeblocks.com/img/pg.png',
    showSelector: true,
  },
  {
    label: 'SQLite',
    value: 'sqlite',
  },
  {
    label: 'Redis',
    value: 'redis',
    icon: 'https://cdn.kubeblocks.com/img/redis.svg',
  },
  {
    label: 'Oracle',
    value: 'oracle',
  },
  {
    label: 'Mongo',
    value: 'mongo',
    icon: 'https://cdn.kubeblocks.com/img/mongodb.svg',
  },
  {
    label: 'ClickHouse',
    value: 'clickhouse',
  },
  {
    label: 'ElasticSearch',
    value: 'elasticsearch',
  },
];

export const DOCUMENT_SOURCE_OPTIONS: TypesDocumentConfigSourceOption[] = [
  {
    label: 'System',
    value: 'system',
  },

  {
    label: 'AWS S3',
    value: 's3',
  },
  {
    label: 'Aliyun OSS',
    value: 'oss',
  },
  {
    label: 'FTP',
    value: 'ftp',
  },
  {
    label: 'Email',
    value: 'email',
  },
];

if (process.env.NODE_ENV === 'development') {
  DOCUMENT_SOURCE_OPTIONS.splice(1, 0, {
    label: 'Local',
    value: 'local',
  });
}

export const COLLECTION_STATUS_TAG_COLORS: {
  [key in TypesCollectionStatus]: PresetStatusColorType;
} = {
  INACTIVE: 'error',
  ACTIVE: 'success',
  DELETED: 'error',
};

export const DOCUMENT_STATUS_TAG_COLORS: {
  [key in TypesDocumentStatus]: PresetStatusColorType;
} = {
  PENDING: 'warning',
  RUNNING: 'processing',
  FAILED: 'error',
  COMPLETE: 'success',
  DELETED: 'default',
};

export const SOCKET_STATUS_MAP: { [key in ReadyState]: TypesSocketStatus } = {
  [ReadyState.CONNECTING]: 'Connecting',
  [ReadyState.OPEN]: 'Open',
  [ReadyState.CLOSING]: 'Closing',
  [ReadyState.CLOSED]: 'Closed',
  [ReadyState.UNINSTANTIATED]: 'Uninstantiated',
};