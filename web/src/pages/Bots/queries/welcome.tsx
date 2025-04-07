import { useIntl, useModel, useParams } from '@umijs/max';
import {
  Row,
  Col,
  Button,
  Card,
  Form,
  Input,
  Typography,
} from 'antd';
import { MinusCircleOutlined, PlusOutlined } from '@ant-design/icons';
import _ from 'lodash';
import { useEffect, useState } from 'react';

export default () => {
  const { formatMessage } = useIntl();
  const { updateBot, getBot } = useModel('bot');
  const { botId } = useParams();
  const bot = getBot(botId);
  const [form] = Form.useForm();

  const onFinish = async () => {
    if (!botId) return;
    const values = form.getFieldsValue();
    _.set(bot, 'config.welcome', values.welcome);
    updateBot(bot.id, bot);
  };

  useEffect(()=>{
    form.setFieldsValue({
      welcome: bot?.config?.welcome,
    });
  },[bot]);

  return (
    <div className="border-block questions">
      <Card bordered={false}>
        <Form form={form} onFinish={onFinish}>
          <Form.Item 
          className="form-item-wrap"
          label='Welcome information'
          name={['welcome','hello']}
          >
            <Input.TextArea autoSize={{minRows:3, maxRows:6}} placeholder={`# Hi, I'm a knowledge assistant.\nYou can ask me like this:`} />
          </Form.Item>
          
          <Form.List name={['welcome','faq']}>
            {(fields, { add, remove }) => (
              <>
                {fields.map(({ key, name, ...restField }) => (
                  <Row key={key} gutter={[8, 8]}>
                    <Col span="22">
                      <Form.Item
                        {...restField}
                        name={[name, 'question']}
                        style={{margin:'0 0 5px'}}
                        rules={[
                          { required: true, message: `${formatMessage({id:'text.question'})}${formatMessage({id:'msg.required'})}`},
                        ]}
                      >
                        <Input placeholder={formatMessage({id:'text.question'})} />
                      </Form.Item>
                      <Form.Item
                        {...restField}
                        name={[name, 'answer']}
                      >
                        <Input.TextArea autoSize={{ minRows: 1, maxRows: 2 }} 
                        placeholder={formatMessage({id:'text.answer_ai'})} />
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
                      <PlusOutlined /> Add FAQ
                    </Typography.Text>
                  }
                />
              </>
            )}
          </Form.List>

          <Form.Item 
          className="form-item-wrap"
          label='Unknown questions response'
          name={['welcome','oops']}>
            <Input.TextArea autoSize={{minRows:3, maxRows:6}} placeholder='Oops, I have no idea about this question, maybe I can answer it after update the newest knowledge.' />
          </Form.Item>
          
          <Form.Item
          style={{ textAlign: 'left', marginTop:'1rem' }}
          className="form-item-wrap"
          >
            <button htmltype="submit">
              {formatMessage({id:"action.update"})}
            </button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
};
