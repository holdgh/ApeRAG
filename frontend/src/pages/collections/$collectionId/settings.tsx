import { Collection } from '@/api';
import { Form } from 'antd';
import _ from 'lodash';
import { toast } from 'react-toastify';
import { useIntl, useModel } from 'umi';
import CollectionForm from '../_form';

export default () => {
  const { formatMessage } = useIntl();
  const [form] = Form.useForm<Collection>();
  const { collection, updateCollection } = useModel('collection');

  const onFinish = async (values: Collection) => {
    const data = _.merge(collection, values);
    const created = await updateCollection(data);
    if (created) {
      toast.success(formatMessage({ id: 'tips.update.success' }));
    }
  };

  if (!collection) {
    return;
  }

  return (
    <CollectionForm
      form={form}
      onSubmit={(values: Collection) => onFinish(values)}
      action="edit"
      values={collection}
    />
  );
};
