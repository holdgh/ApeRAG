import { TypesBot } from '@/types';
import { useModel, useParams } from '@umijs/max';
import BotForm from './form';
import { Form } from 'antd';

export default () => {
  const { updateBot, getBot } = useModel('bot');
  const { botId } = useParams();
  const [form] = Form.useForm();
  const bot = getBot(botId);
  
  if (!bot) return;

  return (
    <div className="border-block">
      <BotForm
        form={form}
        action="edit"
        values={bot}
        onSubmit={(values: TypesBot) => {
          if (!bot.id) return;
          updateBot(bot.id, values);
        }}
      />
    </div>
  );
};
