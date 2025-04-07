import { CreateBot, DeleteBot, GetBots, UpdateBot, ListIntegraions } from '@/services/bots';
import { TypesBot, TypesBotConfig } from '@/types';
import { parseConfig, stringifyConfig } from '@/utils/configParse';
import { history, useModel } from '@umijs/max';
import { App } from 'antd';
import _ from 'lodash';
import { useState } from 'react';

export default () => {
  const [bots, setBots] = useState<TypesBot[]>();
  const [botsLoading, setBotsLoading] = useState<boolean>(false);
  const { collections, setCollections } = useModel('collection');
  const [integrations, setIntegrations] = useState();
  const { message } = App.useApp();

  const getBots = async () => {
    setBotsLoading(true);
    const { data } = await GetBots();

    data.forEach((d) => {
      d.config = parseConfig(d.config as string);
    });

    setBotsLoading(false);
    setBots(data);
  };

  const listIntegraions = async (botId: string) => {
    setBotsLoading(true);
    const { data } = await ListIntegraions(botId);
    setIntegrations(data);
    setBotsLoading(false);
  };

  const getBot = (id?: string): TypesBot | undefined => {
    if (!id) return;
    return bots?.find((c) => String(c.id) === String(id));
  };

  const createBot = async (params: TypesBot) => {
    setBotsLoading(true);
    params.config = stringifyConfig(params.config) as TypesBotConfig;
    const { data, code } = await CreateBot(params);
    setBotsLoading(false);
    if (code === '200' && data.id) {
      data.config = parseConfig(data.config as string);
      message.success('Created successfully');
      await setBots(bots?.concat(data));
      setTimeout(() => history.push(`/bots/${data.id}/chat`));
    } else {

    }
  };

  const updateBot = async (botId: string, params: TypesBot) => {
    setBotsLoading(true);
    params.config = stringifyConfig(params.config) as TypesBotConfig;
    const { code, data } = await UpdateBot(botId, params);

    setBotsLoading(false);

    if (code === '200' && data?.id) {
      data.config = parseConfig(data.config as string);
      message.success('Update completed');
      const index = bots?.findIndex((c) => c.id === botId);
      if (index !== -1 && bots?.length && index !== undefined) {
        _.update(bots, index, (origin) => ({
          ...origin,
          ...data,
        }));
        setBots(bots);
      }
    }
  };

  const deleteBot = async (bot?: TypesBot) => {
    if (!bots || !bot?.id) return;
    const { code } = await DeleteBot(bot.id);
    if (code === '200') {
      setBots(bots.filter((c) => c.id !== bot.id));
      collections?.forEach((collection) => {
        collection.bot_ids = collection.bot_ids?.filter(
          (id) => String(id) !== bot.id,
        );
      });
      setCollections(collections);
      history.push(`/bots`);
    }
  };

  return {
    bots,
    botsLoading,
    integrations,
    getBots,
    getBot,
    updateBot,
    deleteBot,
    createBot,
    listIntegraions,
  };
};
