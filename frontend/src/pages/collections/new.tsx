import { Collection } from '@/api';
import { PageContainer, PageHeader } from '@/components';
import { DOCUMENT_DEFAULT_CONFIG } from '@/constants';
import { Form } from 'antd';
import { toast } from 'react-toastify';
import { history, useIntl, useModel } from 'umi';
import CollectionForm from './_form';

export default () => {
  const { formatMessage } = useIntl();
  const { createCollection } = useModel('collection');
  const [form] = Form.useForm<Collection>();

  const onFinish = async (values: Collection) => {
    const id = await createCollection(values);
    if (id) {
      toast.success(formatMessage({ id: 'tips.create.success' }));
      history.push(`/collections/${id}/documents`);
    }
  };

  return (
    <PageContainer>
      <PageHeader
        title={formatMessage({ id: 'collection.add' })}
        subTitle={formatMessage({ id: 'collection.tips' })}
        backto="/collections"
      />
      <CollectionForm
        form={form}
        onSubmit={(values: Collection) => onFinish(values)}
        action="add"
        values={{
          config: DOCUMENT_DEFAULT_CONFIG,
        }}
      />
    </PageContainer>
  );
};
