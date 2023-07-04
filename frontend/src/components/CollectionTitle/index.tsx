import { COLLECTION_STATUS_TAG_COLORS } from '@/constants';
import type { TypesCollection } from '@/types';
import { AppstoreFilled, ReadFilled } from '@ant-design/icons';
import { Tag, Typography } from 'antd';
import _ from 'lodash';
import styles from './index.less';

type Props = {
  collection?: TypesCollection;
  status?: boolean;
};

export default ({ collection, status }: Props) => {
  return (
    <Typography.Text className={styles.title}>
      {collection?.type === 'document' ? (
        <ReadFilled className={styles.icon} />
      ) : null}
      {collection?.type === 'database' ? (
        <AppstoreFilled className={styles.icon} />
      ) : null}
      {collection?.title}
      {status && collection?.status ? (
        <Tag
          className={styles.status}
          color={COLLECTION_STATUS_TAG_COLORS[collection.status]}
        >
          {_.capitalize(collection?.status)}
        </Tag>
      ) : null}
    </Typography.Text>
  );
};
