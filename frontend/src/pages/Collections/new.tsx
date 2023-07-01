import { PageContainer } from '@ant-design/pro-components';
import { useModel } from '@umijs/max';
import { Card, Form } from 'antd';
import { useEffect } from 'react';
import CollectionForm from './form';

export default () => {
  const [form] = Form.useForm();
  const { createColection } = useModel('collection');

  const onFinish = async () => {
    const values = await form.getFieldsValue();
    createColection(values);
  };

  useEffect(() => {
    form.setFieldValue('type', 'document');
  }, []);

  return (
    <PageContainer ghost>
      <Card bordered={false}>
        <CollectionForm
          onFinish={onFinish}
          form={form}
          type="document"
          action="add"
        />
      </Card>
    </PageContainer>
  );
};
