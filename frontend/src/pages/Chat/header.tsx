import CollectionTitle from '@/components/CollectionTitle';
import { Chat } from '@/models/chat';
import { theme } from 'antd';
import styles from './index.less';

type Props = {
  chat?: Chat;
};

export default ({ chat }: Props) => {
  const { token } = theme.useToken();
  return (
    <div
      className={styles.header}
      style={{ borderBottom: `1px solid ${token.colorBorderSecondary}` }}
    >
      <CollectionTitle collection={chat?.collection} />
    </div>
  );
};
