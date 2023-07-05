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
        background: mask ? '#0A0A0A' : 'transparent',
      }}
    >
      <div className={styles.pageLoading}>
        <div className={styles.message}>KubeChat</div>
      </div>
    </div>
  );
};
