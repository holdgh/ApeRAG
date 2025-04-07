import CollectionForm from '@/pages/Collections/form';
import { TypesCollection } from '@/types';
import { useModel, useParams } from '@umijs/max';
import { Form } from 'antd';
import _ from 'lodash';

export default () => {
  const [form] = Form.useForm()
  const { collectionId } = useParams();
  const { updateCollection, getCollection } = useModel('collection');
  const collection = getCollection(collectionId);

  if (!collection) return;

  return (
    <div className="border-block">
      <CollectionForm
        form={form}
        onSubmit={(values: TypesCollection) => {
          if (!collection.id) return;
          const data = _.merge(collection, values);
          updateCollection(collection.id, data);
        }}
        values={collection}
        action="edit"
      />
    </div>
  );
};
