import classNames from 'classnames';
import _ from 'lodash';
import { ReactNode } from 'react';
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
  const mainNavWidth = 64;
  const hasSidebar = !_.isEmpty(sidebar);
  const subNavWidth = hasSidebar ? 260 : 0;
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
        <div className={styles.top}>
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
