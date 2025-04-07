import { UpdateDocument } from '@/services/documents';
import { TypesDocument, TypesDocumentConfig } from '@/types';
import { stringifyConfig } from '@/utils/configParse';
import { MinusCircleOutlined, PlusOutlined } from '@ant-design/icons';
import { FormattedMessage } from '@umijs/max';
import { App, Button, Col, Form, Input, Modal, Row, Typography } from 'antd';
import { useEffect } from 'react';

type Props = {
  disabled?: boolean;
  collectionId?: string;
  document: TypesDocument;
  onSuccess: (document: TypesDocument) => void;
};

export default ({ collectionId, document, onSuccess, show, cancel }: Props) => {
  const [form] = Form.useForm();
  const { message } = App.useApp();

  const onSave = async () => {
    if (!collectionId) return;
    
    const { labels } = await form.validateFields();
    document.config.labels = labels;

    document.config = stringifyConfig(document.config) as TypesDocumentConfig;
    const res = await UpdateDocument(collectionId, document.id, document);

    if (res.code === '200') {
      onSuccess(document);
      message.success('update success');
    } else {
      message.success('update error');
    }
  };

  useEffect(() => {
    form.setFieldsValue({
      labels: document.config?.labels?.length ? document.config.labels : [{}],
    });
  }, [document]);

  return (
    <>
      <Modal
        title={<FormattedMessage id="text.labels" />}
        open={show}
        onCancel={() => cancel()}
        onOk={async () => {onSave()}}
        forceRender
      >
        <br />
        <Form form={form}>
          <Form.List name="labels">
            {(fields, { add, remove }) => (
              <>
                {fields.map(({ key, name, ...restField }) => (
                  <Row key={key} gutter={[8, 8]}>
                    <Col span="11">
                      <Form.Item
                        {...restField}
                        name={[name, 'key']}
                        rules={[
                          { required: true, message: 'Key is required.' },
                        ]}
                        style={{ marginBottom: 8 }}
                      >
                        <Input placeholder="Key" />
                      </Form.Item>
                    </Col>
                    <Col span="11">
                      <Form.Item
                        {...restField}
                        name={[name, 'value']}
                        rules={[
                          { required: true, message: 'Value is required.' },
                        ]}
                        style={{ marginBottom: 8 }}
                      >
                        <Input placeholder="Value" />
                      </Form.Item>
                    </Col>
                    <Col span="2">
                      <Button
                        onClick={() => remove(name)}
                        block
                        style={{ padding: '4px', textAlign: 'center' }}
                      >
                        <Typography.Text type="secondary">
                          <MinusCircleOutlined />
                        </Typography.Text>
                      </Button>
                    </Col>
                  </Row>
                ))}
                <br />
                <Button
                  type="dashed"
                  onClick={() => add()}
                  block
                  icon={
                    <Typography.Text type="secondary">
                      <PlusOutlined />
                    </Typography.Text>
                  }
                />
              </>
            )}
          </Form.List>
        </Form>
        <br />
        <br />
      </Modal>
    </>
  );
};
