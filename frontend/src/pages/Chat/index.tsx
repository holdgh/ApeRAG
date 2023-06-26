import NoCollections from '@/components/NoCollections';
import { PageContainer } from '@ant-design/pro-components';

const HomePage: React.FC = () => {
  return (
    <PageContainer ghost title={false}>
      <NoCollections />
    </PageContainer>
  );
};

export default HomePage;
