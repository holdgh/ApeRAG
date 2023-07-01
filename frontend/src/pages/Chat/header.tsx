import CollectionTitle from '@/components/CollectionTitle';
import { useModel } from '@umijs/max';
import { Space, theme } from 'antd';
import { ReactNode } from 'react';
import styles from './index.less';

type Props = {
  extra: ReactNode;
};

export default ({ extra }: Props) => {
  const { currentCollection } = useModel('collection');
  const { token } = theme.useToken();

  return (
    <div
      className={styles.header}
      style={{ borderBottom: `1px solid ${token.colorBorderSecondary}` }}
    >
      <Space
        style={{ display: 'flex', justifyContent: 'space-between' }}
        align="center"
      >
        <CollectionTitle collection={currentCollection} />
        {extra}
      </Space>
    </div>
  );
};
