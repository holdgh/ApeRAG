import { Collection } from '@/api';
import { Form } from 'antd';
import { toast } from 'react-toastify';
import { useIntl, useModel } from 'umi';
import CollectionForm from '../_form';

export default () => {
  const { formatMessage } = useIntl();
  const [form] = Form.useForm<Collection>();
  const { collection, updateCollection } = useModel('collection');

  const onFinish = async (values: Collection) => {
    const updated = await updateCollection(values);
    if (updated) {
      toast.success(formatMessage({ id: 'tips.update.success' }));
    }
  };

  return (
    <CollectionForm
      form={form}
      onSubmit={(values: Collection) => onFinish(values)}
      action="edit"
      values={collection}
    />
  );
};
