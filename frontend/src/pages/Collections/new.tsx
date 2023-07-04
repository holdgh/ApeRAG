import type {
  TypesCollection,
  TypesDatabaseConfig,
  TypesDocumentConfig,
} from '@/types';

import {
  CODE_DEFAULT_CONFIG,
  DATABASE_DEFAULT_CONFIG,
  DOCUMENT_DEFAULT_CONFIG,
} from '@/models/collection';

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
    await createColection(values);
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
