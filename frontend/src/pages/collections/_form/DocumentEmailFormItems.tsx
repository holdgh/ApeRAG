import { Col, Form, Input, InputNumber, Row } from 'antd';
import { useIntl } from 'umi';

export default () => {
  const { formatMessage } = useIntl();

  return (
    <>
      <Form.Item
        label={formatMessage({ id: 'email.pop_server' })}
        style={{ marginBottom: 0 }}
        required
      >
        <Row gutter={[8, 0]}>
          <Col span={12}>
            <Form.Item
              name={['config', 'pop_server']}
              rules={[
                {
                  required: true,
                  message: formatMessage({
                    id: 'email.pop_server.url.required',
                  }),
                },
              ]}
            >
              <Input
                placeholder={formatMessage({ id: 'email.pop_server.url' })}
              />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name={['config', 'port']}
              rules={[
                {
                  required: true,
                  message: formatMessage({
                    id: 'email.pop_server.port.required',
                  }),
                },
              ]}
            >
              <InputNumber
                style={{ width: '100%' }}
                placeholder={formatMessage({ id: 'email.pop_server.port' })}
              />
            </Form.Item>
          </Col>
        </Row>
      </Form.Item>
      <Form.Item
        label={formatMessage({ id: 'email.authorize' })}
        style={{ marginBottom: 0 }}
        required
      >
        <Row gutter={[8, 0]}>
          <Col span={12}>
            <Form.Item
              name={['config', 'email_address']}
              rules={[
                {
                  required: true,
                  message: formatMessage({
                    id: 'email.authorize.email_address.required',
                  }),
                },
                {
                  type: 'email',
                  message: formatMessage({
                    id: 'email.authorize.email_address.invalid',
                  }),
                },
              ]}
            >
              <Input
                placeholder={formatMessage({
                  id: 'email.authorize.email_address',
                })}
              />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name={['config', 'email_password']}
              rules={[
                {
                  required: true,
                  message: formatMessage({
                    id: 'email.authorize.email_password.required',
                  }),
                },
              ]}
            >
              <Input.Password
                placeholder={formatMessage({
                  id: 'email.authorize.email_password',
                })}
              />
            </Form.Item>
          </Col>
        </Row>
      </Form.Item>
    </>
  );
};
