import { Col, Form, Input, Row } from 'antd';

import { useIntl } from 'umi';

export default () => {
  const { formatMessage } = useIntl();

  return (
    <>
      <Form.Item
        label={formatMessage({ id: 'feishu.authorize' })}
        style={{ marginBottom: 0 }}
        required
      >
        <Row gutter={[8, 0]}>
          <Col span={12}>
            <Form.Item
              name={['config', 'app_id']}
              rules={[
                {
                  required: true,
                  message: formatMessage({
                    id: 'feishu.authorize.app_id.required',
                  }),
                },
              ]}
            >
              <Input.Password
                placeholder={formatMessage({ id: 'feishu.authorize.app_id' })}
              />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name={['config', 'app_secret']}
              rules={[
                {
                  required: true,
                  message: formatMessage({
                    id: 'feishu.authorize.app_secret.required',
                  }),
                },
              ]}
            >
              <Input.Password
                placeholder={formatMessage({
                  id: 'feishu.authorize.app_secret',
                })}
              />
            </Form.Item>
          </Col>
        </Row>
      </Form.Item>

      <Form.Item
        label={formatMessage({ id: 'feishu.doc_space' })}
        style={{ marginBottom: 0 }}
        required
      >
        <Row gutter={[8, 0]}>
          <Col span={12}>
            <Form.Item
              name={['config', 'space_id']}
              rules={[
                {
                  required: true,
                  message: formatMessage({
                    id: 'feishu.doc_space.space_id.required',
                  }),
                },
              ]}
              required
            >
              <Input
                placeholder={formatMessage({ id: 'feishu.doc_space.space_id' })}
              />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name={['config', 'node_id']}
              rules={[
                {
                  required: true,
                  message: formatMessage({
                    id: 'feishu.doc_space.node_id.required',
                  }),
                },
              ]}
              required
            >
              <Input
                placeholder={formatMessage({ id: 'feishu.doc_space.node_id' })}
              />
            </Form.Item>
          </Col>
        </Row>
      </Form.Item>
    </>
  );
};
