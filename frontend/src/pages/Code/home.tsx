import { CodeOutlined } from '@ant-design/icons';
import { Result, Typography } from 'antd';

export default () => {
  return (
    <Result
      style={{
        marginTop: 100,
      }}
      icon={
        <Typography.Text>
          <CodeOutlined style={{ opacity: 0.1, fontSize: 200 }} />
        </Typography.Text>
      }
      title={
        <Typography.Text strong style={{ fontSize: 80, opacity: 0.1 }}>
          CodeChat
        </Typography.Text>
      }
    />
  );
};
