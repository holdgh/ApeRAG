import NoCollections from '@/components/NoCollections';
import { PageContainer } from '@ant-design/pro-components';

const HomePage: React.FC = () => {
  return (
    <PageContainer ghost>
      <NoCollections />
    </PageContainer>
  );
};

export default HomePage;
