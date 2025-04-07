import { GetChat, GetChats } from '@/services/chats';
import { TypesChat } from '@/types';
import { DislikeFilled, LikeFilled } from '@ant-design/icons';
import { useParams, useIntl, history } from '@umijs/max';
import { Divider, List, Space, Typography, Card, Avatar } from 'antd';
import _ from 'lodash';
import moment from 'moment';
import { useEffect, useState } from 'react';
import QueryEdit from './edit';
import styles from './index.less';
import IconWeb from '@/assets/globe.svg';
import IconFeishu from '@/assets/feishu-on.svg';
import IconWeixin from '@/assets/weixin.svg';
import IconOfficialaccount from '@/assets/officialaccount-on.svg';
import IconDingtalk from '@/assets/dingtalk-on.svg';

export default () => {
  const [dataSource, setDatasource] = useState<TypesChat[]>([]);
  const [groupMessages, setGroupMessages] = useState();
  const [listItems, setListItems] = useState();
  const [listLoading, setListLoading] = useState(false);
  const [queriesLoading, setQueriesLoading] = useState(false);
  const [showQueries, setShowQueries] = useState(false);
  const { botId } = useParams();
  const { formatMessage } = useIntl();

  const loadQueries =async (chatid) => {
    setGroupMessages();
    setShowQueries(true);
    setQueriesLoading(true);
    const res = await GetChat(botId, chatid);
    setDatasource(res.data.history);
    setQueriesLoading(false);
  }

  const loadChats = async () => {
    if (!botId) return;
    setListLoading(true);
    const { data } = await GetChats(botId);
    const items = [];
    data.map((d) => {
      items.push({
        label: d.peer_type==='system' ? 'Console' : `${d.peer_type.replace(/^(.)/,(a,b)=>b.toUpperCase())}_${d.id}`,
        key: d.id,
        peer_type: d.peer_type,
      });
    });
    setListItems(items);
    setListLoading(false);
  };

  const getAvatar = (type) =>{
    switch(type){
      case 'feishu':
        return IconFeishu;
      case 'weixin':
        return IconWeixin;
      case 'dingtalk':
        return IconDingtalk;
      case 'officialaccount':
        return IconOfficialaccount;
      default:
        return IconWeb;
    }
  };

  useEffect(()=>{
    if(dataSource?.length<1){return;}
    const groupMessage = _.map(_.groupBy(dataSource, (chat)=>chat.id), (item)=>{
      const aiMessage = item.find((m) => m.role === 'ai');
      const humanMessage = item.find((m) => m.role === 'human');
      return {
        ...aiMessage,
        ...humanMessage,
        _original_answer: aiMessage?.data,
        revised_answer: aiMessage?.revised_answer,
      };
    });

   setGroupMessages(groupMessage);
   console.log(groupMessage);
  },[dataSource])

  useEffect(() => {
    loadChats();
  }, [history.location.pathname]);

  return (
    <div className="border-block questions">
      <Card bordered={false}>
        <List
          dataSource={listItems}
          loading={listLoading}
          style={{display:showQueries?'none':'block'}}
          renderItem={(item) => (
            <List.Item onClick={()=>{loadQueries(item.key)}} style={{cursor:'pointer'}} className={styles.list}>
              <List.Item.Meta
                style={{alignItems:'center'}}
                avatar={<Avatar src={getAvatar(item.peer_type)} />}
                title={item.label}
              />
            </List.Item>
          )}
        />
        
        <List
            className='queries-list'
            itemLayout="vertical"
            size="large"
            header={<div onClick={()=>{setShowQueries(false)}} style={{cursor:'pointer'}}>&larr; {formatMessage({id:"nav.back"})}</div>}
            loading={queriesLoading}
            style={{display:showQueries?'block':'none'}}
            pagination={{
              onChange: (page) => {
                console.log(page);
              },
              pageSize: 10,
            }}
            dataSource={groupMessages}
            renderItem={(item, idx) => (
              <List.Item
                actions={[]}
                extra={
                  <Space split={<Divider type="vertical" />}>
                    {item.upvote ? (
                      <Typography.Text type="success">
                        <LikeFilled />
                      </Typography.Text>
                    ) : null}

                    {item.downvote ? (
                      <Typography.Text type="danger">
                        <DislikeFilled />
                      </Typography.Text>
                    ) : null}
                    <Typography.Text type="secondary">
                      {moment(item.timestamp).format('llll')}
                    </Typography.Text>
                    <QueryEdit
                      chatId={item.id}
                      record={item}
                      onSuccess={loadChats}
                    />
                  </Space>
                }
              >
                <List.Item.Meta
                  title={item.data}
                  description={item._original_answer || ''}
                />
                {item.revised_answer ? (
                  <Typography.Text type="secondary">
                    {formatMessage({id:'bots.chat.revised'})}: {item.revised_answer}
                  </Typography.Text>
                ) : null}
              </List.Item>
            )}
          />
      </Card>
    </div>
  );
};
