import { SnippetsOutlined } from '@ant-design/icons';
import { Result, Typography } from 'antd';

export default () => {
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
