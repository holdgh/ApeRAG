import { SnippetsOutlined } from '@ant-design/icons';
import { useModel, history } from '@umijs/max';
import { Result, Typography } from 'antd';
import _ from 'lodash';
import { useEffect } from 'react';

export default () => {
  const { currentCollection } = useModel("collection")
  useEffect(() => {
    if(currentCollection?.type === 'document') {
      history.push(`/document/${currentCollection.id}/chat`)
    }
  }, []);
  return (
    <Result
      style={{
        marginTop: 100,
      }}
      icon={
        <Typography.Text>
          <SnippetsOutlined style={{ opacity: 0.1, fontSize: 200 }} />
        </Typography.Text>
      }
      title={
        <Typography.Text strong style={{ fontSize: 80, opacity: 0.1 }}>
          DocChat
        </Typography.Text>
      }
    />
  );
};
