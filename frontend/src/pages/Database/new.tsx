import CollectionForm from '@/components/CollectionForm';
import { DATABASE_DEFAULT_CONFIG } from '@/constants';
import type { TypesCollection } from '@/types';
import { PageContainer } from '@ant-design/pro-components';
import { useModel } from '@umijs/max';
import { Card } from 'antd';

export default () => {
  const { createColection } = useModel('collection');

  return (
    <PageContainer ghost title="Create a connection">
      <Card bordered={false}>
        <CollectionForm
          onSubmit={(values: TypesCollection) => {
            createColection(values);
          }}
          action="add"
          values={{
            type: 'database',
            config: DATABASE_DEFAULT_CONFIG,
          }}
        />
      </Card>
    </PageContainer>
  );
};
