import { DATABASE_TYPE_OPTIONS, DOCUMENT_SOURCE_OPTIONS } from '@/constants';
import {
  TypesCollection,
  TypesDatabaseConfig,
  TypesDocumentConfig,
} from '@/types';
import { history, useModel } from '@umijs/max';
import { Avatar, Divider, Space, Typography } from 'antd';
import classNames from 'classnames';
import moment from 'moment';
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
    const config = collection.config as TypesDatabaseConfig;
    const db = DATABASE_TYPE_OPTIONS.find((o) => o.value === config.db_type);
    return <Avatar size={40} src={db?.icon} />;
  };

  const renderDocumentIcon = () => {
    const config = collection.config as TypesDocumentConfig;
    const item = DOCUMENT_SOURCE_OPTIONS.find((o) => o.value === config.source);
    return (
      <Typography.Text type="secondary" style={{ fontSize: 12 }}>
        {item?.label}
      </Typography.Text>
    );
  };

  const renderDBText = () => {
    const config = collection.config as TypesDatabaseConfig;
    let text = config?.host;
    if (config?.port) {
      text += `:${config?.port}`;
    }
    return text;
  };

  const renderTimestampText = () => {
    return moment(collection.updated).format('llll');
  };

  return (
    <div
      className={classNames({
        [styles.item]: true,
        [styles.selected]: currentCollection?.id === collection.id,
      })}
      onClick={onClick}
    >
      <Space style={{ display: 'flex', width: '100%' }}>
        {collection.type === 'database' ? renderDBIcon() : null}
        <div>
          <Space
            style={{ display: 'flex' }}
            split={<Divider type="vertical" />}
          >
            <Typography.Text
              strong
              ellipsis
              style={{ maxWidth: 140, display: 'block' }}
            >
              {collection.title}
            </Typography.Text>
            {collection.type === 'document' ? renderDocumentIcon() : null}
          </Space>
          <Typography.Text
            type="secondary"
            ellipsis
            style={{ maxWidth: 180, fontSize: 12 }}
          >
            {collection.type === 'database' ? renderDBText() : null}
            {collection.type === 'document' || collection.type === 'code'
              ? renderTimestampText()
              : null}
          </Typography.Text>
        </div>
      </Space>
    </div>
  );
};
