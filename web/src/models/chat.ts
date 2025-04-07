import { CreateChat, GetChat, GetChats } from '@/services/chats';
import { TypesChat, TypesMessage } from '@/types';
import _ from 'lodash';
import { useEffect, useState } from 'react';

export default () => {
  const [chats, setChats] = useState<TypesChat[]>([]);
  const [currentChat, setCurrentChat] = useState<TypesChat>();
  const [chatLoading, setChatLoading] = useState<boolean>(false);

  const createChat = async (botId: string) => {
    const { data } = await CreateChat(botId);
    setCurrentChat(data);
  };

  const getChat = async (botId: string, chatId: string) => {
    let item = _.find(chats, (c) => c.id === chatId);

    if (item) {
      setCurrentChat(item);
    } else {
      const { data } = await GetChat(botId, chatId);
      setChats(chats.concat(data));
      setCurrentChat(data);
    }
  };

  const getChats = async (botId: string) => {
    setChatLoading(true);
    let items = chats.filter((c) => c.bot_id === botId);
    if (_.isEmpty(items)) {
      const { data } = await GetChats(botId);
      items = data;
    }
    const item = _.first(items);
    if (item) {
      await getChat(botId, item.id);
    } else {
      await createChat(botId);
    }
    setChatLoading(false);
  };

  const setCurrentChatHistory = async (data: TypesMessage[]) => {
    if (!currentChat) return;
    setCurrentChat({
      ...currentChat,
      history: data,
    });
  };

  useEffect(() => {
    if (!currentChat) return;
    const index = chats.findIndex((c) => c.id === currentChat.id);
    const items = _.update(chats, index, (origin) => ({
      ...origin,
      ...currentChat,
    }));
    setChats(items);
  }, [currentChat]);

  return {
    chats,
    currentChat,
    chatLoading,
    setCurrentChatHistory,
    getChats,
    getChat,
  };
};
