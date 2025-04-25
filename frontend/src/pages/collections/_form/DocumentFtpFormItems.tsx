import { Col, Form, Input, InputNumber, Row } from 'antd';
import { useIntl } from 'umi';

export default () => {
  const { formatMessage } = useIntl();

  return (
    <>
      <Form.Item
        label={formatMessage({ id: 'ftp.service_address' })}
        style={{ marginBottom: 0 }}
        required
      >
        <Row gutter={[8, 0]}>
          <Col span={12}>
            <Form.Item
              name={['config', 'host']}
              rules={[
                {
                  required: true,
                  message: formatMessage({
                    id: 'ftp.service_address.host.required',
                  }),
                },
              ]}
            >
              <Input
                placeholder={formatMessage({ id: 'ftp.service_address.host' })}
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
                    id: 'ftp.service_address.port.required',
                  }),
                },
              ]}
            >
              <InputNumber
                style={{ width: '100%' }}
                placeholder={formatMessage({ id: 'ftp.service_address.port' })}
              />
            </Form.Item>
          </Col>
        </Row>
      </Form.Item>
      <Form.Item
        label={formatMessage({ id: 'ftp.authorize' })}
        style={{ marginBottom: 0 }}
        required
      >
        <Row gutter={[8, 0]}>
          <Col span={12}>
            <Form.Item
              name={['config', 'username']}
              rules={[
                {
                  required: true,
                  message: formatMessage({
                    id: 'ftp.authorize.username.required',
                  }),
                },
              ]}
            >
              <Input
                placeholder={formatMessage({ id: 'ftp.authorize.username' })}
              />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name={['config', 'password']}
              rules={[
                {
                  required: true,
                  message: formatMessage({
                    id: 'ftp.authorize.password.required',
                  }),
                },
              ]}
            >
              <Input.Password
                placeholder={formatMessage({ id: 'ftp.authorize.password' })}
              />
            </Form.Item>
          </Col>
        </Row>
      </Form.Item>
      <Form.Item
        name={['config', 'path']}
        rules={[
          {
            required: true,
            message: formatMessage({ id: 'ftp.path.required' }),
          },
        ]}
        label={formatMessage({ id: 'ftp.path' })}
      >
        <Input placeholder={formatMessage({ id: 'ftp.path' })} />
      </Form.Item>
    </>
  );
};
