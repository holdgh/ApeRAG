import { useModel, useParams } from '@umijs/max';
import { Card, Form } from 'antd';
import { useEffect } from 'react';
import CollectionForm from './form';

export default () => {
  const [form] = Form.useForm();
  const { collectionId } = useParams();
  const { getCollection, updateCollection } = useModel('collection');

  const collection = getCollection(collectionId);

  const onFinish = async () => {
    if (!collectionId) return;
    const values = await form.getFieldsValue();
    updateCollection(collectionId, {
      ...collection,
      ...values,
    });
  };

  useEffect(() => {
    form.setFieldsValue(collection);
  }, [collection]);

  if (!collection) return;

  return (
    <Card bordered={false}>
      <CollectionForm
        onFinish={onFinish}
        form={form}
        type={collection.type}
        action="edit"
      />
    </Card>
  );
};
