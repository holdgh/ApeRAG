import { getUser } from '@/models/user';
import { FormattedMessage, useModel, useParams } from '@umijs/max';
import { Alert, Card, Col, Form, Input, Row, Typography } from 'antd';
import _ from 'lodash';
import { useEffect } from 'react';

export default () => {
  const { botId } = useParams();
  const { getBot, updateBot } = useModel('bot');
  const [form] = Form.useForm();

  const user = getUser();
  const bot = getBot(botId);

  const onSave = async () => {
    if (!bot || !bot?.id) return;
    const values = await form.validateFields();
    _.set(bot, 'collection_ids', bot?.collections?.map((c) => c.id) || []);
    _.set(bot, 'config.dingtalk', values);
    updateBot(bot.id, bot);
  };

  useEffect(() => {
    form.setFieldsValue(bot?.config?.dingtalk);
  }, []);

  return (
    <Card bordered={false} style={{ minHeight: 400 }}>
      <Form form={form} layout="vertical" onFinish={onSave}>
        {/* <Form.Item
          label={<FormattedMessage id="bots.integration.dingtalk.webhook" />}
          name={['app_webhook']}
        >
          <Input placeholder="Dingtalk Webhook" />
        </Form.Item> */}
        <Form.Item
          label={<FormattedMessage id="text.authorize" />}
          style={{ marginBottom: 0 }}
          required
        >
          <Row gutter={[8, 0]}>
            <Col span={12}>
              <Form.Item
                name={['client_id']}
                rules={[
                  {
                    required: true,
                    message: <FormattedMessage id="text.app_id.help" />,
                  },
                ]}
              >
                <Input.Password placeholder="Dingtalk App ID" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name={['client_secret']}
                rules={[
                  {
                    required: true,
                    message: <FormattedMessage id="text.app_secret.help" />,
                  },
                ]}
              >
                <Input.Password placeholder="Dingtalk App Secret" />
              </Form.Item>
            </Col>
          </Row>
        </Form.Item>
        <Form.Item label="">
          <button htmltype="submit">
            <FormattedMessage id="action.save" />
          </button>
        </Form.Item>
        {bot?.config?.dingtalk ? (
        <>
        <Form.Item label={<FormattedMessage id="bots.integration.dingtalk.url" />}>
          <Alert
            message={
              <Typography.Text
                copyable
                type="secondary"
              >{`${window.location.origin}/api/v1/dingtalk/webhook/event?user=${user?.sub}&bot_id=${botId}`}</Typography.Text>
            }
          />
        </Form.Item>
        </>):null}
      </Form>
    </Card>
  );
};
