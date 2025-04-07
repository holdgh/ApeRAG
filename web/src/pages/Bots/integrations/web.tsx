import { Card, Form, Input, Alert, Typography } from 'antd';
import { useIntl, useModel, useParams } from '@umijs/max';
import { useEffect } from 'react';

export default () => {
  const [form] = Form.useForm();
  const { getBot, updateBot } = useModel('bot');
  const { botId } = useParams();
  const bot = getBot(botId);
  const { formatMessage } = useIntl();

  const onSave = async () => {
    if (!bot || !bot?.id) return;
    const values = await form.validateFields();
    const hosts = values.host_white_list?.split(/\n+/gm);
    values.host_white_list = hosts;
    _.set(bot, 'collection_ids', bot?.collections?.map((c) => c.id) || []);
    _.set(bot, 'config.web', values);
    updateBot(bot.id, bot);
  };

  useEffect(() => {
    form.setFieldValue('host_white_list', bot?.config?.web?.host_white_list?.join('\n'));
  }, []);

  return (
    <Card bordered={false} style={{ minHeight: 400 }}>
      <Form form={form} layout="vertical" onFinish={onSave}>
        <Form.Item
            label={formatMessage({id:"text.host_white_list"})}
            name={['host_white_list']}
            rules={[
              ({ getFieldValue }) => ({
                validator(_, value){
                  const l = value?.match(/^[^\r\n\s]+\n*/gm)?.length;
                  const r = value?.match(/^https?:\/\/[\w\-]+(?:\.[\w\-]+)*(?:\.[\w\-\u4E00-\u9FA5]+|\:\d+)+\n*$/img)?.length;
                  if(l>0 && l===r){
                    return Promise.resolve();
                  }
                  return Promise.reject(formatMessage({id:"text.host_white_list_err"}));
                }
              }),
            ]}
          >
          <Input.TextArea
              autoSize={{ minRows: 2, maxRows: 4 }}
              placeholder= {formatMessage({id:"text.host_white_list_help"})}
            />
        </Form.Item>
        <Form.Item label="">
          <button htmltype="submit">
            {formatMessage({id:"action.save"})}
          </button>
        </Form.Item>
        {bot?.config?.web ? (
        <>
        <Form.Item label={`HTML ${formatMessage({id:'text.usecase'})}`}>
          <Alert
            message={
              <Input.TextArea
                autoSize
                defaultValue={`1. import and mount kubechatComponent
<script crossorigin type="module">
  import kubechatComponent from 'https://cdn.jsdelivr.net/npm/kubechatcomponent@latest/KubechatComponent.js';
  // in case of cdn.jsdelivr.net doesn't work, you can try these cdn: gcore.jsdelivr.net, testingcf.jsdelivr.net 
  // https://unpkg.com/kubechatcomponent@latest/KubechatComponent.js
  kubechatComponent.mount();
</script>

2. use kubechatComponent as a html tag
<kube-chat botid='${botId}' />
`}>
              </Input.TextArea>
            }
          />
        </Form.Item>
        <Form.Item label={`NPM ${formatMessage({id:'text.usecase'})}`}>
          <Alert
            message={
              <Input.TextArea
                autoSize
                defaultValue={`1. install kubechatcomponent
npm install --save kubechatcomponent

2. import and mount kubechatComponent
import kubechatComponent from 'kubechatcomponent';
kubechatComponent.mount();

3. use kubechatComponent as a html tag
<kube-chat botid='${botId}' />
`}>
              </Input.TextArea>
            }
          />
        </Form.Item>
        <Form.Item label={formatMessage({id:'text.customizition'})}>
          <Alert
            message={
              <Input.TextArea
                autoSize
                defaultValue={`1. Customize the bot style

kubechatComponent.mount({customStyle: \`
:host{
  --bg-color-logo: #DAE8F6;
  --text-color: #272727;
  --text-color-tips: #aaa;
  --text-color-input: #272727;
  --text-color-score: #777;
  --bg-color-note: #aaa;
  --border-color-action: #ccc;
  --bg-color-bot: #DAE8F6;
  --bg-color-header: #ACC0E0;
  --bg-color-ref: rgba(0,0,0,0.1);
  --bg-color-answer: #9ABCFF;
  --bg-color-question: #BCD6FC;
}
\`});

2. Specify current user chat session
3. Specify the bot caption text
4. Specify the bot logo image url 
<kube-chat botid='${botId}' session='UUID' title='Bot caption' logo='https://chat.kubeblocks.io/favicon.ico' />
`}>
              </Input.TextArea>
            }
          />
        </Form.Item>
        </>):null}
      </Form>
    </Card>
  );
};
