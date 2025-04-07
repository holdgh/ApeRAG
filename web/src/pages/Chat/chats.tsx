import type { TypesMessage, TypesSocketStatus } from '@/types';
import { history, useIntl, useModel, useParams } from '@umijs/max';
import { useEffect, useState } from 'react';
import MessageItem from './msg';

type Props = {
  status: TypesSocketStatus;
  loading: boolean;
  onExecute: (msg: TypesMessage) => void;
  setStyle: (v: string) => void;
};

export default ({ loading, onExecute, status, extPS, setStyle }: Props) => {
  const intl = useIntl();
  const { currentChat } = useModel('chat');
  const { getBot } = useModel('bot');
  const messages = currentChat?.history || [];
  const [references, setReferences] = useState([]);
  const { botId } = useParams();
  const bot = getBot(botId);
  const closeExtendPanel = () => {
    setStyle('none');
  };
  
  const openExtendPanel = (list) => {
    setReferences(list);
    setStyle('block');
  };

  useEffect(() => {
    setTimeout(() => {
      document.getElementById('message-list')?.scrollIntoView({ behavior: 'smooth', block: 'end' });
      document.getElementById('root')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 1);
  }, [currentChat]);

  if (!bot) return null;

  return (
    <>
      <div className={`main-panel ${extPS}`}>
        <div className="container">
          <div className="hd">
            <div className="title">
              <h6>{bot.title}</h6>
            </div>
            <div className="action">
              <div className="btns">
                <button
                  className="history"
                  title={intl.formatMessage({ id: 'text.queries' })}
                  onClick={() => history.push(`/bots/${bot?.id}/queries`)}
                >
                  {intl.formatMessage({ id: 'text.queries' })}
                </button>
                <button
                  className="deploy"
                  title={intl.formatMessage({ id: 'text.integrations' })}
                  onClick={() => history.push(`/bots/${bot?.id}/integrations`)}
                >
                  {intl.formatMessage({ id: 'text.integrations' })}
                </button>
                <button
                  className="setting"
                  title={intl.formatMessage({ id: 'text.setting' })}
                  onClick={() => history.push(`/bots/${bot?.id}/settings`)}
                >
                  {intl.formatMessage({ id: 'text.setting' })}
                </button>
              </div>
            </div>
          </div>
          <div className="bd">
            {messages.map((item, key) => {
              return (
                <MessageItem
                  openExtendPanel={openExtendPanel}
                  onExecute={onExecute}
                  isTyping={
                    loading &&
                    key === messages.length - 1 &&
                    item.role === 'ai' &&
                    status === 'Open'
                  }
                  key={key}
                  item={item}
                />
              );
            })}
          </div>
        </div>
      </div>
      <div className={`extend-panel ${extPS}`}>
        <div className="container">
          <div className="hd extend-panel-hd">
            <div className="title">
              <h6>{intl.formatMessage({ id: 'text.references' })}</h6>
            </div>
            <div className="action">
              <button className="close" onClick={closeExtendPanel}>
                &times;
              </button>
            </div>
          </div>
          <div className="bd extend-panel-bd">
            {references &&
              references.map((item, index) => (
                <div className="bd-wrap" key={index}>
                  <div className="title-wrap">
                    <div className="index">{index + 1}.</div>
                    <div className="title">{item.metadata?.source}</div>
                    <div className="score">
                      Score: {item.score?.toFixed(2)}
                    </div>
                  </div>
                  <div className="text">{item.text}</div>
                </div>
              ))}
          </div>
        </div>
      </div>
    </>
  );
};
