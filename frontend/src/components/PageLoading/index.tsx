import styles from './index.less';

type Props = {
  message?: string;
};

export default ({ message }: Props) => {
  return (
    <div className={styles.pageLoading}>
      <div className={styles.message}>{message}</div>
    </div>
  );
};
