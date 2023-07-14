import {
  CreateCollectionChat,
  GetCollectionChat,
  GetCollectionChats,
} from '@/services/chats';
import { TypesChat, TypesMessage } from '@/types';
import { useModel } from '@umijs/max';
import _ from 'lodash';
import { useEffect, useState } from 'react';

export default () => {
  const [chats, setChats] = useState<TypesChat[]>([]);
  const [currentChat, setCurrentChat] = useState<TypesChat>();
  const [chatLoading, setChatLoading] = useState<boolean>(false);
  const { currentCollection } = useModel('collection');

  const createChat = async (collectionId: string) => {
    const { data } = await CreateCollectionChat(collectionId);
    data.collectionId = collectionId;
    setCurrentChat(data);
  };

  const getChat = async (collectionId: string, chatId: string) => {
    let item = _.find(chats, (c) => c.id === chatId);

    if (item) {
      setCurrentChat(item);
    } else {
      const { data } = await GetCollectionChat(collectionId, chatId);
      data.collectionId = collectionId;
      setChats(chats.concat(data));
      setCurrentChat(data);
    }
  };

  const getCollectionChats = async (collectionId: string) => {
    setChatLoading(true);
    let items = chats.filter((c) => c.collectionId === collectionId);
    if (_.isEmpty(items)) {
      const { data } = await GetCollectionChats(collectionId);
      items = data;
    }
    const item = _.first(items);
    if (item) {
      await getChat(collectionId, item.id);
    } else {
      await createChat(collectionId);
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
    if (currentCollection?.id) {
      getCollectionChats(currentCollection.id);
    }
  }, [currentCollection]);

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
    currentChat,
    chatLoading,
    setCurrentChatHistory,
  };
};
