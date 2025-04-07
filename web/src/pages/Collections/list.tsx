import DataList from '@/components/Table';
import { useIntl, useModel, useParams, history } from '@umijs/max';
import { useEffect, useState } from 'react';
import Header from '../../components/Header';
import Guide from '../Bots/Guide';
import { Pagination } from 'antd';
import _ from 'lodash';

export default () => {
  const { collections, totalCount, collectionLoading, getCollections } = useModel('collection');

  const [searchValue, setSearchValue] = useState<string>('');
  const [pageSize, setPageSize] = useState<number>(10);
  const [pageNumber, setPageNumber] = useState<number>(1);
  const { formatMessage } = useIntl();

  const { page } = useParams();
  const defaultPage = parseInt(page);

  const headerName = formatMessage({
    id: 'nav.collections',
  });

  const getCollection = async (page, page_size) => {
    const pageId = page || pageNumber;
    const page_Size = page_size || pageSize;
    getCollections(pageId, page_Size);
    setPageNumber(pageId);
  };

  const changePage = (page_number, page_size) => {
    setPageSize(page_size);
    // getCollection(page_number, page_size);
    history.replace(`/collections/${page_number}`);
  };

  const collectionsList: any = collections?.filter(
    (c) => c.title?.match(new RegExp(searchValue, 'i')) || _.isEmpty(searchValue),
  );

  // check collection status
  useEffect(() => {
    getCollection(defaultPage);
  }, [history.location.pathname]);

  if (collections?.length === 0) {
    return (
      <div className="workspace">
        <Header
          name="collections"
          title={headerName}
          page="collections"
          action={false}
          goback={false}
        />
        <div className="bd">
          <Guide
            text="nav.collections.tips"
            classname="collections"
            btn="action.collections.add"
            path="/collections/new"
          />
        </div>
      </div>
    );
  }

  return (
    <div className="workspace">
      <Header
        title={headerName}
        action={true}
        name="collections"
        page="collections"
        path="/collections/new"
        onSetVal={(val: string) => setSearchValue(val)}
      />
      <div className="bd">
        <div className='content'>
          <DataList list={collectionsList} getCollections={getCollection} loading={collectionLoading} />
          {totalCount ? (
            <div className='pagination'>
              <div className='wrap'>
                <Pagination
                  simple
                  total={totalCount}
                  pageSize={pageSize}
                  current={pageNumber}
                  showQuickJumper
                  showSizeChanger
                  onChange={changePage}
                  hideOnSinglePage={true}
                  responsive={true}
                  showTotal={(totalItems) => `${totalItems}${formatMessage({id:'text.items'})}`}
                />
              </div>
            </div>
          ):''}
        </div>
      </div>
    </div>
  );
};
