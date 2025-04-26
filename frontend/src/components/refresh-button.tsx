import { Loading3QuartersOutlined } from '@ant-design/icons';
import { Button, ButtonProps, Tooltip } from 'antd';
import { useIntl } from 'umi';

export const RefreshButton = (props: ButtonProps) => {
  const { formatMessage } = useIntl();
  return (
    <Tooltip title={formatMessage({ id: 'action.refresh' })}>
      <Button {...props} type="text" icon={<Loading3QuartersOutlined />} />
    </Tooltip>
  );
};
