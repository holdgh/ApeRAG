import { PageContainer } from '@/components';
import { Button, Result, theme } from 'antd';
import { UndrawPeopleSearch } from 'react-undraw-illustrations';
import { FormattedMessage, Link } from 'umi';

export default () => {
  const { token } = theme.useToken();

  return (
    <PageContainer>
      <Result
        icon={
          <UndrawPeopleSearch
            primaryColor={token.colorPrimary}
            height="200px"
          />
        }
        title="404"
        subTitle={<FormattedMessage id="text.pageNotFound" />}
        extra={
          <Link to="/">
            <Button type="primary">
              <FormattedMessage id="action.backToHome" />
            </Button>
          </Link>
        }
      />
    </PageContainer>
  );
};
