import CollectionTitle from '@/components/CollectionTitle';
import { theme } from 'antd';
import styles from './index.less';
import { useModel } from '@umijs/max';

export default () => {
  const { currentCollection } = useModel("collection")
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
