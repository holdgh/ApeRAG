import { Collection } from '@/api';
import { PageContainer, PageHeader } from '@/components';
import { DOCUMENT_DEFAULT_CONFIG } from '@/constants';
import { api } from '@/services';
import { stringifyConfig } from '@/utils';
import { Form } from 'antd';
import _ from 'lodash';
import { toast } from 'react-toastify';
import { history, useIntl, useModel } from 'umi';
import CollectionForm from './_form';

export default () => {
  const { formatMessage } = useIntl();
  const { setLoading } = useModel('global');
  const [form] = Form.useForm<Collection>();

  const onFinish = async (values: Collection) => {
    const data = _.merge(
      {
        type: 'document',
        config: DOCUMENT_DEFAULT_CONFIG,
      },
      values,
    );

    data.config = stringifyConfig(data.config) as string;
    setLoading(true);
    const res = await api.collectionsPost({ collectionCreate: data });
    setLoading(false);
    if (res.data.id) {
      toast.success(formatMessage({ id: 'tips.create.success' }));
      history.push(`/collections/${res.data.id}/documents`);
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
          config: DOCUMENT_DEFAULT_CONFIG as string,
        }}
      />
    </PageContainer>
  );
};
