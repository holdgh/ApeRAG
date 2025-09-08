import { Chat } from '@/api';
import {
  PageContainer,
  PageContent,
} from '@/components/page-container';
import { getServerApi } from '@/lib/api/server';
import _ from 'lodash';
import { getTranslations } from 'next-intl/server';
import { redirect } from 'next/navigation';
import { BotHeader } from './bot-header';

export default async function Page({
  params,
}: Readonly<{
  params: Promise<{ botId: string }>;
}>) {
  const apiServer = await getServerApi();
  const page_bot = await getTranslations('page_bot');
  const { botId } = await params;
  const chatsRes = await apiServer.defaultApi.botsBotIdChatsGet({
    botId,
    page: 1,
    pageSize: 1,
  });

  //@ts-expect-error api define has a bug
  const chat: Chat | undefined = _.first(chatsRes.data.items || []);

  if (chat) {
    redirect(`/bots/${botId}/chats/${chat.id}`);
  } else {
    // const res = await apiServer.defaultApi.botsBotIdChatsPost({
    //   botId,
    //   chatCreate: {
    //     title: '',
    //   },
    // });
    // if (res.data.id) {
    //   redirect(`/bots/${botId}/chats/${res.data.id}`);
    // }
  }

  return (
    <PageContainer>
      <BotHeader
        breadcrumbs={[{ title: page_bot('metadata.title'), href: `/bots` }]}
        extra=""
      />
      <PageContent></PageContent>
    </PageContainer>
  );
}
