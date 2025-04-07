import themeVariable from '@/variable';
import { CSSProperties } from 'react';
import styles from './index.less';

type Props = {
  mask?: boolean;
  style?: CSSProperties | undefined;
};

export default ({ mask = true, style = {} }: Props) => {
  return (
    <div
      className={styles.mask}
      style={{
        ...style,
        background: mask ? themeVariable.backgroundColor : 'transparent',
      }}
    >
      <div className={styles.pageLoading}>
        <div className={styles.message}>{SITE_TITLE}</div>
      </div>
    </div>
  );
};
