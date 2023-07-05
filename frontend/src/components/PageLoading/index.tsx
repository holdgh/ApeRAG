import styles from './index.less';

type Props = {
  mask?: boolean;
};

export default ({ mask = true }: Props) => {
  return (
    <div
      className={styles.mask}
      style={{
        background: mask ? '#0A0A0A' : 'transparent',
      }}
    >
      <div className={styles.pageLoading}>
        <div className={styles.message}>KubeChat</div>
      </div>
    </div>
  );
};
