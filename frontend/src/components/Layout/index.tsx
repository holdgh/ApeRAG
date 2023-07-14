import { useModel, useParams } from '@umijs/max';
import { theme } from 'antd';
import classNames from 'classnames';
import _ from 'lodash';
import { ReactNode, useEffect } from 'react';
import styles from './index.less';

type Props = {
  sidebar?: {
    title?: ReactNode;
    content?: ReactNode;
    extra?: ReactNode;
  };
  children?: ReactNode;
};

export default ({ sidebar, children }: Props) => {
  const { collectionId } = useParams();
  const { getCollection, setCurrentCollection } = useModel('collection');

  const mainNavWidth = 64;
  const hasSidebar = !_.isEmpty(sidebar);
  const subNavWidth = hasSidebar ? 260 : 0;
  const { token } = theme.useToken();

  useEffect(() => {
    const collection = getCollection(collectionId);
    if (collection) {
      setCurrentCollection(collection);
    }
  }, [collectionId]);

  return (
    <div
      className={classNames({
        [styles.layout]: true,
      })}
      style={{
        paddingLeft: hasSidebar ? subNavWidth : 0,
      }}
    >
      <div
        className={styles.sidebar}
        style={{
          width: subNavWidth,
          left: mainNavWidth,
        }}
      >
        <div
          className={styles.top}
          style={{ borderBottom: `1px solid ${token.colorBorderSecondary}` }}
        >
          <div className={styles.title}>{sidebar?.title}</div>
          <div className={styles.extra}>{sidebar?.extra}</div>
        </div>
        <div className={styles.content}>{sidebar?.content}</div>
      </div>
      <div className={styles.content} style={{ padding: 0 }}>
        {children}
      </div>
    </div>
  );
};
