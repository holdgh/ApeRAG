import type {
  TypesCollection,
  TypesDatabaseConfig,
  TypesDocumentConfig,
} from '@/models/collection';

import { DOCUMENT_DEFAULT_CONFIG } from '@/models/collection';

import { PageContainer } from '@ant-design/pro-components';
import { useModel } from '@umijs/max';
import { Card, Form } from 'antd';
import _ from 'lodash';
import { useEffect } from 'react';
import CollectionForm from './form';

export default () => {
  const [form] = Form.useForm();
  const { createColection } = useModel('collection');

  const onFinish = async () => {
    const values = await form.getFieldsValue();
    createColection(values);
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
    form.setFieldsValue(DOCUMENT_DEFAULT_CONFIG);
  }, []);

  return (
    <PageContainer ghost>
      <Card bordered={false}>
        <CollectionForm
          onValuesChange={onValuesChange}
          onFinish={onFinish}
          form={form}
          type="document"
          action="add"
        />
      </Card>
    </PageContainer>
  );
};
