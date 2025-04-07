import Header from '@/components/Header';
import { SOCKET_STATUS_MAP } from '@/constants';
import { getUser } from '@/models/user';
import { UpdateChat } from '@/services/chats';
import type { TypesMessage, TypesMessageReferences } from '@/types';
import { useModel, useParams, history } from '@umijs/max';
import classNames from 'classnames';
import _ from 'lodash';
import { useEffect, useState } from 'react';
import useWebSocket from 'react-use-websocket';
import Chats from './chats';
import Footer from './footer';
import styles from './index.less';

export default () => {
  const user = getUser();
  const { botId } = useParams();
  const [extendPanelStyle, setExtendPanelStyle] = useState('none');
  // the data stream in the loading state
  const [isTyping, setIsTyping] = useState<boolean>(false);
  const [disabled, setDisabled] = useState<boolean>(false);

  // websocket url & params
  const [socketUrl, setSocketUrl] = useState<string | null>(null);

  // model data;
  const { bots, getBots, getBot } = useModel('bot');
  const { currentChat, setCurrentChatHistory, getChats } = useModel('chat');

  // history list;
  const historyMessages = currentChat?.history || [];

  // web socket instance
  const { sendJsonMessage, lastJsonMessage, readyState } = useWebSocket(
    socketUrl,
    {
      share: true,
      protocols: user?.__raw,
      shouldReconnect: () => true,
      reconnectInterval: 5000,
      reconnectAttempts: 10,
    },
  );

  let bot = getBot(botId);

  const updateSocketUrl = () => {
    if (!currentChat || botId !== currentChat?.bot_id) return;

    const protocol =
      window.location.origin.indexOf('https') > -1 ? 'wss' : 'ws';
    const hostname = window.location.origin.replace(/^(http|https):\/\//, '');
    let url = `${protocol}://${hostname}/api/v1/bots/${botId}/chats/${currentChat.id}/connect`;

    setSocketUrl(url);
  };

  const onExecute = async (msg: TypesMessage) => {
    sendJsonMessage(msg);
  };

  const onClear = async () => {
    if (!bot?.id || !currentChat?.id) return;
    const { data } = await UpdateChat(bot.id, currentChat.id, {
      ...currentChat,
      history: [],
    });
    if (data.id) setCurrentChatHistory([]);
  };

  const onSubmit = async (data: string) => {
    if (isTyping) return;
    console.log(data, 'submit msg 1');
    const timestamp = new Date().getTime();
    const msg: TypesMessage = {
      type: 'message',
      role: 'human',
      data,
      timestamp,
    };
    console.log(msg, 'submit msg 2');
    historyMessages.push(msg);
    await setCurrentChatHistory(historyMessages);
    console.log(historyMessages, 'submit msg 3');
    sendJsonMessage(msg);
    console.log(historyMessages, 'submit msg 4');
  };

  useEffect(() => {
    if(!bots){
      getBots();
      bot = getBot(botId);
    }
    if(currentChat){
      _.set(currentChat, 'history', []);
    }
    if (botId) {
      getChats(botId);
    }
  }, [history.location.pathname]);

  useEffect(() => {
    updateSocketUrl();
  }, [currentChat]);

  useEffect(() => {
    if (_.isEmpty(lastJsonMessage)) return;

    const msg: TypesMessage = {
      ...lastJsonMessage,
      role: 'ai',
      _typeWriter: true,
    };

    let index = historyMessages.findLastIndex((m) => m.id === msg.id);
    if (index === -1) {
      index = 0;
    }
    
    // set history references when all stream has been received.
    if (msg.type === 'stop') {
      setIsTyping(false);
      const references = msg.data as unknown as TypesMessageReferences[];
      if (msg.data) {
        _.update(historyMessages, index, (origin) => ({
          ...origin,
          references,
        }));
        setCurrentChatHistory(historyMessages);
      }
      return;
    }

    // create a new message or update an old message.
    if (msg.type === 'welcome') {
      setIsTyping(false);
      if(historyMessages.length>0){return;}
      const welcome = msg.data?.hello + `<i class="faq">${msg.data.faq.join('</i><i class="faq">')}</i>`;
      _.set(msg, 'data', welcome);
      historyMessages.push(msg);
    }else if (msg.type === 'start') {
      setIsTyping(true);
      historyMessages.push(msg);
    } else {
      _.update(historyMessages, index, (origin) => ({
        ...msg,
        data: (origin?.data || '') + msg.data, // append new stream data
      }));
    }
    setCurrentChatHistory(historyMessages);
    setDisabled(false);
  }, [lastJsonMessage]);

  if (!bot) return null;

  document.body.addEventListener('click', async (e)=>{
    const dom = e.target;
    const tag = dom.tagName.toLowerCase();
    const cls = dom.className;
    if((tag === 'button' && cls.match('show-reference'))||(tag === 'div' && cls.match(/text|title|score/i))){
      e.stopImmediatePropagation();
      return;
    }
    if(tag==='i' && cls==='faq'){
      e.stopImmediatePropagation();
      await onSubmit(dom.textContent);
    }
    setExtendPanelStyle('none');
  });

  return (
    <div className="workspace chat">
      <Header goback={true} />
      <div className="bd">
        <div className="content">
          <div className={`bots-detail ${extendPanelStyle}`} id="message-list">
            <Chats
              loading={isTyping}
              status={SOCKET_STATUS_MAP[readyState]}
              onExecute={onExecute}
              extPS = {extendPanelStyle}
              setStyle={setExtendPanelStyle}
            />

            <div
              className={`footer-wrap ${classNames({
                [styles.footer]: true,
              })}`}
            >
              <Footer
                isTyping={isTyping}
                disabled={disabled}
                status={SOCKET_STATUS_MAP[readyState]}
                onSubmit={onSubmit}
                onClear={onClear}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
