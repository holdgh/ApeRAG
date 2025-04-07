import { useIntl,history } from '@umijs/max';
import './index.less';

interface IListProps {
  type: string;
  list: any;
  loading: boolean;
}

const CustomList = (props: IListProps) => {
  const { type, list, loading } = props;
  const classname = type === 'table' ? `data-list table` : 'data-list';
  const { formatMessage } = useIntl();
  return (
    <div className={`${classname} ${loading?'waiting':''}`}>
      <ul>
        <li className='header'>
            <div className="cell">Bot</div>
            <div className="cell">Collections</div>
        </li>
        <li className='column'>
            <div className="cell"></div>
            <div className="cell"></div>
        </li>
        {list &&
          list.map((item: any) => {
            return (
              <li key={item.id} className='row' onClick={(e)=>{history.push(`/bots/${item.id}/chat`)}}>
                  <div className="cell title">
                    <h5>{item.title}</h5>
                  </div>
                  <div className="cell describe">
                    <strong>{item.type==='common' ? formatMessage({id:"text.bot.type.common"}) : formatMessage({id:"text.bot.type.knowledge"})}</strong>
                    {item.system ? `(${formatMessage({id:"text.system.builtin"})})` :''}
                  </div>
              </li>
            );
          })}
      </ul>
    </div>
  );
};

export default CustomList;
