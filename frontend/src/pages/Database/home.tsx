import { ConsoleSqlOutlined } from '@ant-design/icons';
import { useModel, history } from '@umijs/max';
import { Result, Typography } from 'antd';
import { useEffect } from 'react';

export default () => {
  const { currentCollection } = useModel("collection")
  useEffect(() => {
    if(currentCollection?.type === 'database') {
      history.push(`/database/${currentCollection.id}/chat`)
    }
  }, []);
  return (
    <Result
      style={{
        marginTop: 100,
      }}
      icon={
        <Typography.Text>
          <ConsoleSqlOutlined style={{ opacity: 0.1, fontSize: 200 }} />
        </Typography.Text>
      }
      title={
        <Typography.Text strong style={{ fontSize: 80, opacity: 0.1 }}>
          SQLChat
        </Typography.Text>
      }
    />
  );
};
