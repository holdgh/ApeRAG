import { theme } from 'antd';
import classNames from 'classnames';
import _ from 'lodash';
import { ReactNode } from 'react';
import styles from './index.less';

type Props = {
  sidebar?: {
    title?: ReactNode;
    width?: number | string;
    content?: ReactNode;
    extra?: ReactNode;
  };
  content?: {
    padding: number;
  };
  children?: ReactNode;
};

export default ({ sidebar, content, children }: Props) => {
  const { token } = theme.useToken();
  const mainNavWidth = 65;
  const hasSidebar = !_.isEmpty(sidebar);
  const subNavWidth = hasSidebar ? 260 : 0;
  const borderColor = 'rgba(255, 255, 255, 0.05)';
  const contentPadding = content?.padding || '24px 40px';

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
          background: token.colorBgContainer,
        }}
      >
        <div className={styles.top} style={{ borderBottom: `1px solid ${borderColor}` }}>
          <div className={styles.title}>{sidebar?.title}</div>
          <div className={styles.extra}>{sidebar?.extra}</div>
        </div>
        <div className={styles.content}>
          { sidebar?.content }
        </div>
      </div>
      <div
        className={styles.content}
        style={{ padding: contentPadding }}
      >
        {children}
      </div>
    </div>
  );
};
