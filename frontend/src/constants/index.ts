import {
  TypesCollectionStatus,
  TypesDatabaseConfig,
  TypesDatabaseConfigDbTypeOption,
  TypesDocumentConfig,
  TypesDocumentConfigSourceOption,
  TypesDocumentStatus,
  TypesSocketStatus,
} from '@/types';
import { PresetStatusColorType } from 'antd/es/_util/colors';
import { ReadyState } from 'react-use-websocket';

export const DOCUMENT_DEFAULT_CONFIG: TypesDocumentConfig = {
  source: 'system',
};

export const DATABASE_DEFAULT_CONFIG: TypesDatabaseConfig = {
  verify: 'prefered',
  db_type: 'mysql',
};

export const CODE_DEFAULT_CONFIG = {};

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
    icon: 'https://cdn.kubeblocks.com/img/sqlite.png',
  },
  {
    label: 'Redis',
    value: 'redis',
    icon: 'https://cdn.kubeblocks.com/img/redis.svg',
  },
  {
    label: 'Oracle',
    value: 'oracle',
    icon: 'https://cdn.kubeblocks.com/img/oracle.png',
  },
  {
    label: 'Mongo',
    value: 'mongo',
    icon: 'https://cdn.kubeblocks.com/img/mongodb.svg',
  },
  {
    label: 'ClickHouse',
    value: 'clickhouse',
    icon: 'https://cdn.kubeblocks.com/img/clickhouse.png',
  },
  {
    label: 'ElasticSearch',
    value: 'elasticsearch',
    icon: 'https://cdn.kubeblocks.com/img/elasticsearch.png',
  },
];

export const DOCUMENT_SOURCE_OPTIONS: TypesDocumentConfigSourceOption[] = [
  {
    label: 'File Upload',
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
    label: 'Local Path',
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
