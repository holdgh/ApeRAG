import { ApeNode } from '@/types';
import Icon, { QuestionCircleOutlined } from '@ant-design/icons';
import { Space, Tag, theme, Tooltip, Typography } from 'antd';
import { TbVariable } from 'react-icons/tb';
export const ApeNodeGlobal = ({ node }: { node: ApeNode }) => {
  const { token } = theme.useToken();
  return (
    <div style={{ width: 260 }}>
      <Space style={{ display: 'flex' }}>
        <Icon viewBox="0 0 14 14" style={{ color: token.blue }}>
          <TbVariable />
        </Icon>
        <Typography>全局变量</Typography>
      </Space>
      {node.data.vars?.map((item, index) => {
        return (
          <Space
            key={index}
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              marginBlock: 8,
            }}
          >
            <Space style={{ display: 'flex', alignItems: 'center' }}>
              <Typography.Text>{item.name}</Typography.Text>
              <Tooltip title={item.description}>
                <QuestionCircleOutlined />
              </Tooltip>
            </Space>
            <Tag color={token.colorPrimary}>{item.type}</Tag>
          </Space>
        );
      })}
    </div>
  );
};
