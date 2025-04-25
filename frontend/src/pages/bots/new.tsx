import { Bot } from '@/api';
import { PageContainer, PageHeader } from '@/components';
import { api } from '@/services';
import { stringifyConfig } from '@/utils';
import { Card, Form } from 'antd';
import { history, useIntl } from 'umi';
import BotForm from './_form';

export default () => {
  const { formatMessage } = useIntl();
  const [form] = Form.useForm<Bot>();

  const onFinish = async (values: Bot) => {
    const botRes = await api.botsPost({
      botCreate: {
        ...values,
        config: stringifyConfig(values.config),
      },
    });
    if (botRes.data.id) {
      await api.botsBotIdChatsPost({
        botId: botRes.data.id,
        chatCreate: {
          title: '',
        },
      });
      history.push('/bots');
    }
  };

  return (
    <PageContainer>
      <PageHeader
        backto="/bots"
        title={formatMessage({ id: 'bot.add' })}
        subTitle={formatMessage({ id: 'bot.description' })}
      />
      <Card variant="borderless">
        <BotForm
          form={form}
          onSubmit={(values: Bot) => onFinish(values)}
          action="add"
          values={{
            type: 'knowledge',
          }}
        />
      </Card>
    </PageContainer>
  );
};
