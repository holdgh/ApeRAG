import Loading from '@/loading';
import { FormattedMessage } from 'umi';
import styles from './loading.less';

export default () => {
  return (
    <>
      <div className={styles.mask}>
        <div className={styles.loading}>
          <div className={styles.message}>
            <FormattedMessage id="text.authorizing" />
          </div>
        </div>
      </div>
      <Loading />
    </>
  );
};
