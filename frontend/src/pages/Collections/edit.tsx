
import type {
  TypesCollection,
  TypesDatabaseConfig,
  TypesDocumentConfig,
} from '@/types';
import { useModel, useParams } from '@umijs/max';
import { Card, Form } from 'antd';
import _ from 'lodash';
import { useEffect } from 'react';
import CollectionForm from './form';
import { CODE_DEFAULT_CONFIG, DATABASE_DEFAULT_CONFIG, DOCUMENT_DEFAULT_CONFIG } from '@/constants';

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

  const onValuesChange = (changedValues: TypesCollection) => {
    if (changedValues.type) {
      let config: TypesDocumentConfig & TypesDatabaseConfig = {};
      if (changedValues.type === 'database' && _.isEmpty(config.host)) {
        form.setFieldValue('config', DATABASE_DEFAULT_CONFIG.config);
      }
      if (changedValues.type === 'document' && _.isEmpty(config.source)) {
        form.setFieldValue('config', DOCUMENT_DEFAULT_CONFIG.config);
      }
      if (changedValues.type === 'code' && _.isEmpty(config.source)) {
        form.setFieldValue('config', CODE_DEFAULT_CONFIG.config);
      }
    }
  };
  
  useEffect(() => {
    if (collection?.type === 'document') {
      form.setFieldsValue({
        ...DOCUMENT_DEFAULT_CONFIG,
        ...collection,
      });
    }
    if (collection?.type === 'database') {
      form.setFieldsValue({
        ...DATABASE_DEFAULT_CONFIG,
        ...collection,
      });
    }
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
