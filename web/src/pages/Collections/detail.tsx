import Header from '@/components/Header';
import {
  FormattedMessage,
  Outlet,
  history,
  useModel,
  useParams,
  useIntl,
} from '@umijs/max';
import { App, Tabs, TabsProps, Typography } from 'antd';
import { useEffect, useState } from 'react';

export default () => {
  const { user } = useModel('user');
  const { collectionId, page } = useParams();
  const [activeKey, setActiveKey] = useState<string>();
  const [currentPage, setCurrentPage] = useState(page);
  const { collections, getCollection, getCollections, deleteCollection } = useModel('collection');
  const [ collection, setCollection ] = useState<any>();
  const [ readonly, setReadonly ] = useState(false);
  const { modal } = App.useApp();
  const { formatMessage } = useIntl();

  const getAllCollections = async () => {
    if(collections){return;}
    getCollections(1, null);
  };

  let config = collection?.config;

  const onDelete = () => {
    if (!collectionId) return;
    modal.confirm({
      title: formatMessage({ id: 'text.delete.help' }),
      content: <>{formatMessage({ id: 'text.collections' })}: {collection?.title}<br/>{formatMessage({ id: 'text.delete.confirm' })}</>,
      onOk: async () => {
        await deleteCollection(collection);
      },
      okButtonProps: {
        danger: true,
      },
    });
  };

  const items: TabsProps['items'] = [
    { 
      label: <FormattedMessage id="text.documents" />, 
      key: currentPage?`documents/${currentPage}`:'documents',
    },
    {
      label: <FormattedMessage id="text.sync" />,
      key: 'sync',
      disabled: config?.source === 'system' || readonly,
    },
    { label: <FormattedMessage id="text.setting" />, 
      key: 'settings',
      disabled: readonly,
    },
    {
      label: <FormattedMessage id="text.related_question" />,
      key: 'questions',
      disabled: readonly,
    }
  ];

  useEffect(() => {
    if(page){
      setCurrentPage(page);
    }
    const key = history.location.pathname.match(/[^\/]+(?:\/\d+)?$/i)?.[0];
    setActiveKey(key);
  }, [history.location]);

  useEffect(() => {
    if (!activeKey) return;

    getAllCollections();
    
    if (activeKey.match(/documents\/\d+$/i)) {
      history.replace(`/collections/${collectionId}/${activeKey}`);
    } else if(['documents', 'sync', 'settings', 'questions'].includes(activeKey)) {
      history.replace(`/collections/${collectionId}/${activeKey}`);
    } else {
      history.replace(page?`/collections/${collectionId}/documents/${page}`:`/collections/${collectionId}/documents`);
    }

  }, [activeKey]);

  useEffect(()=>{
    const collectionDetail = getCollection(collectionId);
    setCollection(collectionDetail);
    setReadonly(collectionDetail?.system && !user?.is_admin);
  }, [collections])

  return (
    <div className="workspace">
      <Header
        goback={true}
        title={collection?.title}
        name="collections"
        page="collections-detele"
        action={readonly?false:onDelete}
      />
      <div className='bd'>
        <div className='content'>
          {(collection?.description || collection?.system) ? (
            <Typography.Paragraph type="secondary">
              {collection?.description}
              { collection?.system ? 
                collection?.description ? 
                `(${formatMessage({id:"text.system.builtin"})})`
                : formatMessage({id:"text.system.builtin"})
                : ''}
            </Typography.Paragraph>
          ) : null}
          <Tabs
            className="custom-tabs"
            items={items}
            activeKey={activeKey}
            onChange={(key) => {setActiveKey(key);}}
          />
          <Outlet />
        </div>
      </div>
    </div>
  );
};
