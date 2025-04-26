import { ApeCollection } from '@/types';
import { Form } from 'antd';
import _ from 'lodash';
import { toast } from 'react-toastify';
import { useIntl, useModel } from 'umi';
import CollectionForm from '../_form';

export default () => {
  const { formatMessage } = useIntl();
  const [form] = Form.useForm<ApeCollection>();
  const { collection, updateCollection } = useModel('collection');
  const { setLoading } = useModel('global');

  const onFinish = async (values: ApeCollection) => {
    const data = _.merge(collection, values);
    setLoading(true);
    const created = await updateCollection(data);
    setLoading(false);
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
      onSubmit={(values: ApeCollection) => onFinish(values)}
      action="edit"
      values={collection}
    />
  );
};
