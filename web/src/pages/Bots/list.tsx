import { useIntl, useModel, history } from '@umijs/max';
import _ from 'lodash';
import { useState, useEffect } from 'react';
import Guide from './Guide';
import Header from '../../components/Header';
import CustomList from './List/index';

export default () => {
  const { botsLoading,getBots } = useModel('bot');
  const { getModels } = useModel('model');
  const intl = useIntl();
  const { bots } = useModel('bot');
  const [searchValue, setSearchValue] = useState<string>('');
  const headerName = intl.formatMessage({
    id: 'nav.bots',
  });

  useEffect(() => {
    getBots();
    getModels();
  }, [history.location.pathname]);
  
  const botList: any = bots?.filter(
    (c) => c.title?.match(new RegExp(searchValue,'i')) || _.isEmpty(searchValue),
  );
  
  // 表单空状态
  if (bots?.length === 0) {
    return (
      <div className='workspace'>
        <Header
          title={headerName} 
          name="bots" 
          page="bots"
          action={false} 
          goback={false} 
        />
        <div className='bd'>
          <div className='content'>
            <Guide
              text="bots.guide.text"
              classname="bots"
              btn="action.bots.add"
              path="/bots/new"
            />
          </div>
        </div>
      </div>
    );
  }
  // 列表
  return (
    <div className='workspace'>
      <Header
        title={headerName}
        action={true}
        name="bots"
        page="bots"
        path="/bots/new"
        onSetVal={(val: string) => setSearchValue(val)}
      />
      <div className='bd'>
        <div className='content'>
          <CustomList type="list" list={botList} loading={botsLoading} />
        </div>
      </div>
    </div>
  );
};
