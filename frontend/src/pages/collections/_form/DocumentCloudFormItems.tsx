import { MinusCircleOutlined, PlusOutlined } from '@ant-design/icons';
import { Button, Col, Form, Input, Row, Typography } from 'antd';
import { useIntl } from 'umi';

export default () => {
  const { formatMessage } = useIntl();

  return (
    <>
      <Form.Item
        name={['config', 'region']}
        rules={[
          {
            required: true,
            message: formatMessage({ id: 'cloud.region.required' }),
          },
        ]}
        label={formatMessage({ id: 'cloud.region' })}
      >
        <Input
          placeholder={formatMessage({ id: 'cloud.region.placeholder' })}
        />
      </Form.Item>
      <Form.Item
        label={formatMessage({ id: 'cloud.authorize' })}
        style={{ marginBottom: 0 }}
        required
      >
        <Row gutter={[8, 0]}>
          <Col span={12}>
            <Form.Item
              name={['config', 'access_key_id']}
              rules={[
                {
                  required: true,
                  message: formatMessage({
                    id: 'cloud.authorize.access_key_id.required',
                  }),
                },
              ]}
            >
              <Input.Password
                placeholder={formatMessage({
                  id: 'cloud.authorize.access_key_id',
                })}
              />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name={['config', 'secret_access_key']}
              rules={[
                {
                  required: true,
                  message: formatMessage({
                    id: 'cloud.authorize.secret_access_key.required',
                  }),
                },
              ]}
            >
              <Input.Password
                placeholder={formatMessage({
                  id: 'cloud.authorize.secret_access_key',
                })}
              />
            </Form.Item>
          </Col>
        </Row>
      </Form.Item>

      <Form.Item
        label={formatMessage({ id: 'cloud.bucket' })}
        style={{ marginBottom: 0 }}
        required
      >
        <Form.List name={['config', 'buckets']} initialValue={[{}]}>
          {(fields, { add, remove }) => (
            <>
              {fields.map(({ key, name }) => (
                <Row key={key} gutter={[8, 0]}>
                  <Col span={11}>
                    <Form.Item
                      name={[name, 'bucket']}
                      rules={[
                        {
                          required: true,
                          message: formatMessage({
                            id: 'cloud.bucket.required',
                          }),
                        },
                      ]}
                    >
                      <Input
                        placeholder={formatMessage({
                          id: 'cloud.bucket.placeholder',
                        })}
                      />
                    </Form.Item>
                  </Col>
                  <Col span={11}>
                    <Form.Item
                      name={[name, 'dir']}
                      rules={[
                        {
                          required: true,
                          message: formatMessage({
                            id: 'cloud.bucket.directory.required',
                          }),
                        },
                      ]}
                    >
                      <Input
                        placeholder={formatMessage({
                          id: 'cloud.bucket.directory',
                        })}
                      />
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
              <Button
                type="dashed"
                onClick={() => add()}
                block
                icon={
                  <Typography.Text type="secondary">
                    <PlusOutlined /> {formatMessage({ id: 'cloud.bucket.add' })}
                  </Typography.Text>
                }
              />
            </>
          )}
        </Form.List>
      </Form.Item>
    </>
  );
};
