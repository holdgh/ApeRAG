import { PageContainer, PageHeader } from '@/components';

import { useIntl } from 'umi';

export default () => {
  const { formatMessage } = useIntl();
  return (
    <PageContainer>
      <PageHeader
        title={formatMessage({ id: 'model.provider' })}
        description={formatMessage({ id: 'model.provider.description' })}
      />
    </PageContainer>
  );
};
