import { ReactNode } from 'react';
import styles from './index.less';

type Props = {
  title?: ReactNode;
  extra?: ReactNode;
  content?: ReactNode;
};

export default ({ title, extra, content }: Props) => {
  return (
    <div className={styles.fixedHeader}>
      <div className={styles.header}>
        <div className={styles.title}>{title}</div>
        <div>{extra}</div>
      </div>
      {content}
    </div>
  );
};
