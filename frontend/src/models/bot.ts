import { Chat, ChatDetails } from '@/api';
import { api } from '@/services';
import { ApeBot, BotConfig } from '@/types';
import { parseConfig } from '@/utils';
import { useState } from 'react';
import { useModel } from 'umi';
import { parse } from 'yaml';

export default () => {
  const { setLoading } = useModel('global');

  const [bot, setBot] = useState<ApeBot>();
  const [botLoading, setBotLoading] = useState<boolean>(false);

  const [bots, setBots] = useState<ApeBot[]>();
  const [botsLoading, setBotsLoading] = useState<boolean>(false);

  const [chat, setChat] = useState<ChatDetails>();

  const [chats, setChats] = useState<Chat[]>();
  const [chatsLoading, setChatsLoading] = useState<boolean>(false);

  // bots
  const getBots = async () => {
    setLoading(true);
    setBotsLoading(true);
    const res = await api.botsGet();

    setLoading(false);
    setBotsLoading(false);
    setBots(
      res.data.items?.map((item) => ({
        ...item,
        config: parseConfig(item.config),
      })),
    );
  };

  // bot
  const getBot = async (botId: string) => {
    setLoading(true);
    setBotLoading(true);
    const res = await api.botsBotIdGet({ botId });

    setLoading(false);
    setBotLoading(false);

    const config: BotConfig = parseConfig(res.data.config);

    if (config.flow) {
      config.flow = parse(config.flow as unknown as string);
    }
    setBot({
      ...res.data,
      config,
    });
  };

  // chats
  const getChats = async (botId: string) => {
    setLoading(true);
    setChatsLoading(true);
    const res = await api.botsBotIdChatsGet({ botId });
    setLoading(false);
    setChatsLoading(false);
    setChats(res.data.items);
  };

  // chat
  const getChat = async (botId: string, chatId: string) => {
    setLoading(true);
    const res = await api.botsBotIdChatsChatIdGet({
      botId,
      chatId,
    });
    setLoading(false);
    setChat(res.data);
  };

  return {
    bot,
    botLoading,
    getBot,
    setBot,

    bots,
    botsLoading,
    getBots,
    setBots,

    chats,
    chatsLoading,
    getChats,
    setChats,

    chat,
    getChat,
    setChat,
  };
};
