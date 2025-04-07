import { FormattedMessage, history, useIntl, useModel, useParams } from '@umijs/max';
interface IHeaderProps {
  page?: string;
  path?: string;
  title?: string;
  goback?: boolean;
  action?: any;
  name?: string;
  onSetVal?: (e: any) => void;
}

const Header = (props: IHeaderProps) => {
  const intl = useIntl();
  const { title, goback, action, path, onSetVal, page, name } = props;
  const isBots = name ? name === 'bots' : false;
  const { botsLoading } = useModel('bot');
  const { collectionsLoading } = useModel('collection');

  const placeholder = intl.formatMessage({
    id: isBots ? 'bots.search.bots' : 'bots.search.collections',
  });

  const addButton = intl.formatMessage({
    id: isBots ? 'bots.add.bots.btn' : 'action.collections.add',
  });

  const gobackLink = (
    <div className="bread">
      <button onClick={() => window.history.back()}>
        &larr; <FormattedMessage id="nav.back" />
      </button>
    </div>
  );

  let actionPanel = '';

  switch (page) {
    case 'chat-bot':
      const { botId } = useParams();
      actionPanel = (
        <div className="action chat-bot">
            <button
              className="history"
              title={intl.formatMessage({ id: 'text.queries' })}
              onClick={() => history.push(`/bots/${botId}/queries/welcome`)}
            >
              {intl.formatMessage({ id: 'text.queries' })}
            </button>
            <button
              className="deploy"
              title={intl.formatMessage({ id: 'text.integrations' })}
              onClick={() => history.push(`/bots/${botId}/integrations`)}
            >
              {intl.formatMessage({ id: 'text.integrations' })}
            </button>
            <button
              className="setting"
              title={intl.formatMessage({ id: 'text.setting' })}
              onClick={() => history.push(`/bots/${botId}/settings`)}
            >
              {intl.formatMessage({ id: 'text.setting' })}
            </button>
        </div>
      );
      break;
    case 'bots-new':
      actionPanel = (
        <div className="action">
          <button
            onClick={action}
            disabled={botsLoading}
            className={botsLoading ? 'waiting' : ''}
          >
            <FormattedMessage id="action.create" />
          </button>
        </div>
      );
      break;
    case 'collections-new':
      actionPanel = (
        <div className="action">
          <button
            onClick={action}
            disabled={collectionsLoading}
            className={botsLoading ? 'waiting' : ''}
          >
            <FormattedMessage id="action.create" />
          </button>
        </div>
      );
      break;
    case 'collections-detele':
      actionPanel = (
        <div className="action" onClick={action}>
          <i className='delete-icon'></i>
        </div>
      );
      break;
    case 'dev-settings':
      actionPanel = (
        <div className="action" onClick={action}>
          <button>
            <FormattedMessage id="text.newkey" />
          </button>
        </div>
      );
      break;
    default:
      actionPanel = (
        <div className="action">
          <label className="search">
            <input
              type="text"
              placeholder={placeholder}
              onChange={(e) => onSetVal && onSetVal(e.currentTarget.value)}
            />
          </label>
          <button onClick={() => path && history.push(path)}>
            + {addButton}
          </button>
        </div>
      );
  }
  
  return (
    <>
      <div className="hd">
        {goback && gobackLink}
        <div className="title">
          <h2>{title}</h2>
        </div>
        {action && actionPanel}
      </div>
    </>
  );
};

export default Header;
