import CollectionTitle from '@/components/CollectionTitle';
import { useModel } from '@umijs/max';
import { theme } from 'antd';
import styles from './index.less';

export default () => {
  const { currentCollection } = useModel('collection');
  const { token } = theme.useToken();
  return (
    <div
      className={styles.header}
      style={{ borderBottom: `1px solid ${token.colorBorderSecondary}` }}
    >
      <CollectionTitle collection={currentCollection} />
    </div>
  );
};
