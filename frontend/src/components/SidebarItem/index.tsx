import { DATABASE_TYPE_OPTIONS } from '@/constants';
import {
  TypesCollection,
  TypesDatabaseConfig,
  TypesDocumentConfig,
} from '@/types';
import { history, useModel } from '@umijs/max';
import { Avatar, Space, Tag, Typography } from 'antd';
import classNames from 'classnames';
import styles from './index.less';

type Props = {
  collection: TypesCollection;
};

export default ({ collection }: Props) => {
  const { setCurrentCollection, currentCollection } = useModel('collection');
  const onClick = async () => {
    await setCurrentCollection(collection);
    setTimeout(() => {
      history.push(`/${collection.type}/${collection.id}/chat`);
    }, 100);
  };

  const renderDBIcon = () => {
    if (collection.type === 'database') {
      const config = collection.config as TypesDatabaseConfig;
      const db = DATABASE_TYPE_OPTIONS.find((o) => o.value === config.db_type);
      return <Avatar size={50} src={db?.icon} />;
    }
  };
  const renderDBText = () => {
    if (collection.type === 'database') {
      const config = collection.config as TypesDatabaseConfig;
      return (
        <Typography.Text type="secondary">
          {config?.host}
          {config?.port ? `:${config?.port}` : ''}
        </Typography.Text>
      );
    }
  };

  const renderDocumentTag = () => {
    if (collection.type === 'document') {
      const config = collection.config as TypesDocumentConfig;
      return <Tag>{config.source}</Tag>;
    }
  };

  return (
    <div
      className={classNames({
        [styles.item]: true,
        [styles.selected]: currentCollection?.id === collection.id,
      })}
      onClick={onClick}
    >
      <Space style={{ display: 'flex' }}>
        {renderDBIcon()}
        <Space direction="vertical" size="small">
          <Space size="small">
            {renderDocumentTag()}
            <Typography.Text
              ellipsis
              style={{ maxWidth: 160, display: 'block' }}
            >
              {collection.title} {}
            </Typography.Text>
          </Space>
          {renderDBText()}
        </Space>
      </Space>
    </div>
  );
};
