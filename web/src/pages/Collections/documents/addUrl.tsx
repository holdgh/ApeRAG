import { createCollectionUrls } from '@/services';
import { TypesCollection } from '@/types';
import { MinusCircleOutlined, PlusOutlined } from '@ant-design/icons';
import { FormattedMessage } from '@umijs/max';
import { Button, Col, Form, Input, Modal, Row } from 'antd';
import { useEffect, useState } from 'react';

type Props = {
  collection: TypesCollection;
  onSuccess: () => void;
};

export default ({ collection, onSuccess }: Props) => {
  const [loading, setLoading] = useState<boolean>(false);
  const [visible, setVisible] = useState<boolean>(false);
  const [form] = Form.useForm();

  const onSave = async () => {
    const values = await form.validateFields();
    if (!collection.id) return;
    const { code } = await createCollectionUrls(collection.id, values);
    if (code === '200') {
      setVisible(false);
      onSuccess();
    }
    setLoading(false);
  };

  useEffect(() => {
    form.setFieldValue('urls', [{}]);
  }, []);

  return (
    <>
      <Button
        onClick={() => setVisible(true)}
        disabled={collection?.system}
        type="primary"
        loading={loading}
      >
        <FormattedMessage id="action.documents.addUrl" />
      </Button>
      <Modal
        title={<FormattedMessage id="action.documents.addUrl" />}
        open={visible}
        onCancel={() => setVisible(false)}
        onOk={() => onSave()}
        forceRender
      >
        <Form form={form} style={{ marginTop: 30 }}>
          <Form.List name="urls">
            {(fields, { add, remove }) => {
              return (
                <>
                  {fields.map(({ key, name, ...restField }) => (
                    <Row key={key} gutter={[8, 8]}>
                      <Col span={21}>
                        <Form.Item
                          {...restField}
                          name={[name, 'url']}
                          style={{ marginBottom: 8 }}
                          rules={[
                            { required: true, message: 'url is required' },
                          ]}
                        >
                          <Input placeholder="URL" />
                        </Form.Item>
                      </Col>
                      <Col span={3}>
                        <Button block onClick={() => remove(name)}>
                          <MinusCircleOutlined />
                        </Button>
                      </Col>
                    </Row>
                  ))}
                  <Form.Item>
                    <Button
                      type="dashed"
                      onClick={() => add()}
                      block
                      icon={<PlusOutlined />}
                    >
                      Add URL
                    </Button>
                  </Form.Item>
                </>
              );
            }}
          </Form.List>
        </Form>
      </Modal>
    </>
  );
};
