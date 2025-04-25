import { PageContainer } from '@/components';
import { Result, theme } from 'antd';
import { UndrawWorking } from 'react-undraw-illustrations';

export default () => {
  const { token } = theme.useToken();

  return (
    <PageContainer>
      <Result
        icon={
          <UndrawWorking primaryColor={token.colorPrimary} height="200px" />
        }
        title="401"
        subTitle="Unauthorized"
      />
    </PageContainer>
  );
};
