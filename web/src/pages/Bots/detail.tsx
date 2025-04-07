import Header from '@/components/Header';
import {
  FormattedMessage,
  Outlet,
  history,
  useModel,
  useParams,
  useIntl,
} from '@umijs/max';
import { App, Tabs, TabsProps } from 'antd';
import { useEffect, useState } from 'react';

export default () => {
  const { botId } = useParams();
  const [activeKey, setActiveKey] = useState<string>();
  const { bots, getBots, getBot, deleteBot } = useModel('bot');
  const { user } = useModel('user');
  const { models, getModels } = useModel('model');
  const { modal } = App.useApp();
  const { formatMessage } = useIntl();
  const [ bot, setBot ] = useState<any>();
  const [ readonly, setReadonly ] = useState(true);

  const onDelete = () => {
    if (!botId) return;
    modal.confirm({
      title: formatMessage({ id: 'text.delete.help' }),
      content: <>{formatMessage({ id: 'text.bots' })}: {bot?.title}<br/>{formatMessage({ id: 'text.delete.confirm' })}</>,
      onOk: async () => {
        await deleteBot(bot);
      },
      okButtonProps: {
        danger: true,
      },
    });
  };

  const items: TabsProps['items'] = [
    {
      label: <FormattedMessage id="text.queries" />,
      key: activeKey?.match(/queries/i) ? activeKey : 'queries/welcome',
      disabled: readonly,
    },
    {
      label: <FormattedMessage id="text.integrations" />,
      key: 'integrations',
      disabled: readonly,
    },
    { 
      label: <FormattedMessage id="text.setting" />, 
      key: 'settings',
      disabled: readonly,
    },
  ];

  useEffect(()=>{
    if(!bots){
      getBots();
    }
    if(bot){
      setReadonly(bot.system && !user.is_admin);
    }else{
      setBot(getBot(botId));
    }
  },[bots,bot,user]);

  useEffect(() => {
    if(!bots){
      getBots();
      setBot(getBot(botId));
    }
    if(!models || !models.length){
      getModels();
    }
    const key = history.location.pathname.replace(/.*\//g, '');
    if(key==='welcome'){
      setActiveKey('queries/welcome');
    }else if(key==='platform'){
      setActiveKey('queries/platform');
    }else{
      setActiveKey(key);
    }
  }, [history.location.pathname]);

  useEffect(() => {
    if (!activeKey || readonly) return;

    if (['integrations', 'queries', 'queries/welcome', 'queries/platform', 'settings'].includes(activeKey)) {
      if(activeKey==='queries/welcome'||activeKey==='queries'){
        history.replace(`/bots/${botId}/queries/welcome`);
      }else if(activeKey==='queries/platform'){
        history.replace(`/bots/${botId}/queries/platform`);
      }else{
        history.replace(`/bots/${botId}/${activeKey}`);
      }
    } else {
      history.replace(`/bots/${botId}/settings`);
    }
  }, [activeKey]);

  return (
    <div className="workspace">
      <Header
        goback={true}
        title={bot?.title}
        name="bots-new"
        page="collections-detele"
        action={() => onDelete()}
      />
      <div className="bd">
        <div className="content">
          <Tabs
            className="custom-tabs"
            items={items}
            activeKey={!readonly ? activeKey : ''}
            onChange={(key) => setActiveKey(key)}
          />
          { !readonly && (
          <Outlet />
          )}
        </div>
      </div>
    </div>
  );
};
