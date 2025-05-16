import { ApeNode, ApeNodeConfig } from '@/types';
import { QuestionCircleOutlined } from '@ant-design/icons';
import { Input, InputProps, theme } from 'antd';
import { useIntl } from 'umi';
import { StyledFlowNodeAvatar } from './_styles';

export const ConnectInfoInput = ({
  refNode,
  refNodeConfig,
  ...props
}: InputProps & {
  refNodeConfig?: ApeNodeConfig;
  refNode?: ApeNode;
}) => {
  const { token } = theme.useToken();
  const { formatMessage } = useIntl();
  return (
    <Input
      {...props}
      variant="filled"
      placeholder={formatMessage({
        id: 'flow.connection.required',
      })}
      prefix={
        <StyledFlowNodeAvatar
          size="small"
          shape="square"
          token={token}
          color={refNodeConfig?.color}
          src={refNodeConfig?.icon || <QuestionCircleOutlined />}
        />
      }
      value={
        refNode
          ? refNode?.ariaLabel ||
            formatMessage({
              id: `flow.node.type.${refNode?.type}`,
            })
          : ''
      }
    />
  );
};
