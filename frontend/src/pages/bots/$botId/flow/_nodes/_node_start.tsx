import { ApeNode } from '@/types';
import { theme, Typography } from 'antd';
import { useIntl } from 'umi';
import { OutputParams } from './_outputs_params';
import { StyledFlowNodeSection } from './_styles';

export const ApeNodeStart = ({ node }: { node: ApeNode }) => {
  const { token } = theme.useToken();
  const { formatMessage } = useIntl();

  return (
    <StyledFlowNodeSection token={token}>
      <Typography.Paragraph>
        {formatMessage({ id: 'flow.variable.global' })}
      </Typography.Paragraph>
      <OutputParams node={node} />
    </StyledFlowNodeSection>
  );
};
