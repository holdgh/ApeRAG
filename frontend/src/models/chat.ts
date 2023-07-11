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

  const createChat = async () => {
    if (!currentCollection?.id) return;
    const { data } = await CreateCollectionChat(currentCollection.id);
    data.collectionId = currentCollection.id;
    setCurrentChat(data);
  };

  const getChat = async (id: string) => {
    if (!currentCollection?.id) return;
    let item = _.find(chats, (c) => c.id === id);

    if (item) {
      setCurrentChat(item);
    } else {
      const { data } = await GetCollectionChat(currentCollection.id, id);
      data.collectionId = currentCollection.id;
      setChats(chats.concat(data));
      setCurrentChat(data);
    }
  };

  const getCollectionChats = async () => {
    if (!currentCollection?.id) return;
    setChatLoading(true);
    let items = chats.filter((c) => c.collectionId === currentCollection.id);
    if (_.isEmpty(items)) {
      const { data } = await GetCollectionChats(currentCollection.id);
      items = data;
    }
    const item = _.first(items);
    if (item) {
      await getChat(item.id);
    } else {
      await createChat();
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
    getCollectionChats();
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
