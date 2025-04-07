import { getUser } from '@/models/user';
import { useIntl, useModel, useParams } from '@umijs/max';
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
    _.set(bot, 'config.weixin', values);
    updateBot(bot.id, bot);
  };

  const {formatMessage} = useIntl();

  useEffect(() => {
    form.setFieldsValue(bot?.config?.weixin);
  }, []);

  return (
    <Card bordered={false} style={{ minHeight: 400 }}>
      <Form form={form} layout="vertical" onFinish={onSave}>
        <Form.Item
          label={formatMessage({id:"text.encrypt_key"})}
          required
        >
          <Row gutter={[8, 0]}>
            <Col span={12}>
              <Form.Item
                name={['api_encoding_aes_key']}
                rules={[
                  {
                    required: true,
                    message: `EncodingAESKey${formatMessage({id:"msg.required"})}`,
                  },
                ]}
              >
                <Input.Password placeholder="App Receive Messages EncodingAESKey" />
              </Form.Item>
            </Col>
            <Col span={12}>
                <Form.Item
                  name={['api_token']}
                  rules={[
                    {
                      required: true,
                      message: `Token${formatMessage({id:"msg.required"})}`,
                    },
                  ]}
                >
                  <Input.Password placeholder="App Receive Messages Token" />
                </Form.Item>
              </Col>
          </Row>
        </Form.Item>
        <Form.Item
          label={formatMessage({id:"text.authorize"})}
          required
        >
          <Row gutter={[8, 0]}>
            <Col span={12}>
              <Form.Item
                name={['app_id']}
                rules={[
                  {
                    required: true,
                    message: `App ID${formatMessage({id:"msg.required"})}`,
                  },
                ]}
              >
                <Input placeholder="App Agent ID" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name={['app_secret']}
                rules={[
                  {
                    required: true,
                    message: `App Secret${formatMessage({id:"msg.required"})}`,
                  },
                ]}
              >
                <Input.Password placeholder="App Secret" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={[8, 0]}>
            <Col span={12}>
              <Form.Item
                name={['corp_id']}
                rules={[
                  {
                    required: true,
                    message: `Corp ID${formatMessage({id:"msg.required"})}`,
                  },
                ]}
              >
                <Input placeholder="Corp ID" />
              </Form.Item>
            </Col>
            
          </Row>
        </Form.Item>
        <Form.Item label="">
          <button htmltype="submit">
          {formatMessage({id:"action.save"})}
          </button>
        </Form.Item>
        {bot?.config?.weixin ? (
        <>
        <Form.Item label={formatMessage({id:"bots.integration.weixin.url"})}>
          <Alert
            message={
              <Typography.Text
                copyable
                type="secondary"
              >{`${window.location.origin}/api/v1/weixin/webhook/event?user=${user?.sub}&bot_id=${botId}`}</Typography.Text>
            }
          />
        </Form.Item>
        <Form.Item label={formatMessage({id:"bots.integration.trust_ip"})}>
          <Alert
            message={
              <Typography.Text
                copyable
                type="secondary"
              >18.183.6.122,54.249.130.113</Typography.Text>
            }
          />
        </Form.Item>
        </>):null}
      </Form>
    </Card>
  );
};
