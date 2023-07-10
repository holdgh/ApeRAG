import CollectionForm from '@/components/CollectionForm';
import { TypesCollection } from '@/types';
import { useModel, useParams } from '@umijs/max';
import { Card } from 'antd';

export default () => {
  const { collectionId } = useParams();
  const { updateCollection, getCollection } = useModel('collection');
  const collection = getCollection(collectionId);

  if (!collection) return;

  return (
    <Card bordered={false}>
      <CollectionForm
        onSubmit={(values: TypesCollection) => {
          if (!collection.id) return;
          updateCollection(collection.id, values);
        }}
        values={collection}
        action="edit"
      />
    </Card>
  );
};