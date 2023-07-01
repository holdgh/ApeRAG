import { DOCUMENT_DEFAULT_CONFIG } from '@/models/collection';
import type {
  TypesCollection,
  TypesDatabaseConfig,
  TypesDocumentConfig,
} from '@/types';
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

  const onValuesChange = (
    changedValues: TypesCollection,
    allValues: TypesCollection,
  ) => {
    if (changedValues.type) {
      let config: TypesDocumentConfig & TypesDatabaseConfig = {};
      if (allValues.config) {
        try {
          JSON.parse(allValues.config);
        } catch (err) {}
      }
      if (changedValues.type === 'database' && _.isEmpty(config.host)) {
        form.setFieldValue('config', '');
      }
      if (changedValues.type === 'document' && _.isEmpty(config.source)) {
        form.setFieldValue('config', DOCUMENT_DEFAULT_CONFIG);
      }
    }
  };

  useEffect(() => {
    form.setFieldsValue(collection);
  }, [collection]);

  if (!collection) return;

  return (
    <Card bordered={false}>
      <CollectionForm
        onFinish={onFinish}
        onValuesChange={onValuesChange}
        form={form}
        type={collection.type}
        action="edit"
      />
    </Card>
  );
};
