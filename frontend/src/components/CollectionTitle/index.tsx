import type { TypesCollection } from '@/types';
import { AppstoreOutlined, ReadOutlined } from '@ant-design/icons';
import { Tag, Typography } from 'antd';

import { COLLECTION_STATUS_TAG_COLORS } from '@/models/collection';
import _ from 'lodash';
import styles from './index.less';

type Props = {
  collection?: TypesCollection;
  status: boolean;
};

export default ({ collection, status }: Props) => {
  return (
    <Typography.Text className={styles.title}>
      {collection?.type === 'document' ? (
        <ReadOutlined className={styles.icon} />
      ) : null}
      {collection?.type === 'database' ? (
        <AppstoreOutlined className={styles.icon} />
      ) : null}
      {collection?.title}
      {status && collection?.status ? (
        <Tag className={styles.status} color={COLLECTION_STATUS_TAG_COLORS[collection.status]}>
          {_.capitalize(collection?.status)}
        </Tag>
      ) : null}
    </Typography.Text>
  );
};
