import _ from 'lodash';
import moment from 'moment';
import { getSourceItemByValue } from '@/constants';
import { useIntl,useModel,history } from '@umijs/max';
import { useEffect } from 'react';

function DataList({ list, getCollections, loading }) {
  const { user } = useModel('user');
  const { formatMessage } = useIntl();

  useEffect(() => {
    let allStatusReady = true;
    if (list) {
      list.forEach((item) => {
        if(item.status?.match(/INACTIVE/i)){
          allStatusReady = false;
        }
      });
    }

    const timer = setTimeout(()=>{
      if(allStatusReady){return;}
      getCollections();
    }, 2000);

    return () => {  
      clearTimeout(timer);  
    };
  }, [list]);

  return (
    <div className={`data-list table collections ${loading?'waiting':''}`}>
      <ul>
        <li className="header">
            <div className="cell title">
              {formatMessage({id: 'text.collections'})}
            </div>
            <div className="cell">
              {formatMessage({id: 'text.source'})}
            </div>
            <div className="cell">
              {formatMessage({id: 'text.status'})}
            </div>
            <div className="cell">
              {formatMessage({id: 'text.document.updatedAt'})}
            </div>
        </li>
        <li className='column'>
            <div className="cell title"></div>
            <div className="cell"></div>
            <div className="cell"></div>
            <div className="cell"></div>
        </li>
        {list &&
          list.map((item, index) => {
            return (
              <li key={item.id} className='row' onClick={(e)=>{history.push(`/collections/${item.id}/documents`)}}>
                  <div className="cell title">
                    <h5>
                      {item.title}
                    </h5>
                  </div>
                  <div className="cell describe">
                    { item.system && !user.is_admin
                      ? formatMessage({id:'text.system.builtin'})
                      : getSourceItemByValue(item.config?.source)?.label
                    }
                  </div>
                  <div className="cell">
                    <label className={`label-status ${item.status}`}>{item.status}</label>
                  </div>
                  <div className="cell time">
                    {moment(item.created).fromNow()}
                  </div>
              </li>
            );
          })}
      </ul>
    </div>
  );
}

export default DataList;
