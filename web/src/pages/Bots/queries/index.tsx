import { useParams, useIntl, history, Outlet } from '@umijs/max';
import { Tabs, TabsProps } from 'antd';
import _ from 'lodash';
import { useEffect, useState } from 'react';

export default () => {
  const [activeKey, setActiveKey] = useState('welcome');
  const { botId } = useParams();
  const { formatMessage } = useIntl();

  const changeQuery = (key) => {
    setActiveKey(key);
    if(key==='welcome'){
      history.replace(`/bots/${botId}/queries/welcome`);
    }else{
      history.replace(`/bots/${botId}/queries/platform`);
    }
  };

  const items: TabsProps['items'] = [{
    label: formatMessage({id:'text.welcome'}),
    key: 'welcome',
  },{
    label: formatMessage({id:'text.platform'}),
    key: 'platform',
  }];

  useEffect(()=>{
    const key = history.location.pathname.replace(/.*\//g, '');
    setActiveKey(key);
  },[history.location.pathname]);

  return (
    <>
      <Tabs
        items={items}
        activeKey={activeKey}
        onChange={changeQuery}
      />
      <Outlet />
    </>
  );
};
