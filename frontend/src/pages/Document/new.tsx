import CollectionForm from '@/components/CollectionForm';
import { DOCUMENT_DEFAULT_CONFIG } from '@/constants';
import type { TypesCollection } from '@/types';
import { PageContainer } from '@ant-design/pro-components';
import { useModel } from '@umijs/max';
import { Card, Form } from 'antd';

export default () => {
  const [form] = Form.useForm();
  const { createColection } = useModel('collection');

  return (
    <PageContainer ghost title="Create a collection">
      <Card bordered={false}>
        <CollectionForm
          onSubmit={(values: TypesCollection) => {
            createColection(values);
          }}
          form={form}
          action="add"
          values={{
            type: 'document',
            config: DOCUMENT_DEFAULT_CONFIG,
          }}
        />
      </Card>
    </PageContainer>
  );
};
