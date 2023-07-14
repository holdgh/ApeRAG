import { DATABASE_TYPE_OPTIONS, DOCUMENT_SOURCE_OPTIONS } from '@/constants';
import {
  TypesCollection,
  TypesDatabaseConfig,
  TypesDocumentConfig,
} from '@/types';
import { Link, useModel } from '@umijs/max';
import { Avatar, Divider, Space, Typography, theme } from 'antd';
import classNames from 'classnames';
import moment from 'moment';
import styles from './index.less';

type Props = {
  collection: TypesCollection;
};

export default ({ collection }: Props) => {
  const { token } = theme.useToken();
  const { currentChat } = useModel('chat');

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
    return moment(collection.updated).format('lll');
  };

  return (
    <Link
      className={classNames({
        [styles.item]: true,
        [styles.selected]: currentChat?.collectionId === collection.id,
      })}
      style={{
        borderBottom: `1px solid ${token.colorBorderSecondary}`,
      }}
      to={`/${collection?.type}/${collection?.id}/chat`}
    >
      <Space style={{ display: 'flex', width: '100%' }}>
        {collection.type === 'database' ? renderDBIcon() : null}
        <div>
          <Space style={{ display: 'flex' }}>
            <Typography.Text
              strong
              ellipsis
              style={{ maxWidth: 200, display: 'block' }}
            >
              {collection.title}
            </Typography.Text>
          </Space>
          <Space split={<Divider type="vertical" />} size="small">
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
            {collection.type === 'document' ? renderDocumentIcon() : null}
          </Space>
        </div>
      </Space>
    </Link>
  );
};
