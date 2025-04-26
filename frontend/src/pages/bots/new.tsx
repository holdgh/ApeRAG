import { Bot } from '@/api';
import { PageContainer, PageHeader } from '@/components';
import { api } from '@/services';
import { stringifyConfig } from '@/utils';
import { Card, Form } from 'antd';
import { history, useIntl, useModel } from 'umi';
import BotForm from './_form';

export default () => {
  const { formatMessage } = useIntl();
  const [form] = Form.useForm<Bot>();

  const { setLoading } = useModel('global');

  const onFinish = async (values: Bot) => {
    setLoading(true);
    const botRes = await api.botsPost({
      botCreate: {
        ...values,
        config: stringifyConfig(values.config),
      },
    });
    setLoading(false);
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
