import { FormattedMessage, useModel, useParams, useIntl, history } from '@umijs/max';
import {
  App,
  Pagination,
  Card,
  Upload,
  UploadProps,
} from 'antd';
import _ from 'lodash';
import { useEffect, useState } from 'react';
import AddUrl from './addUrl';
import Documentlist from '@/components/DocumentTable';

export default () => {
  const { user } = useModel('user');
  const { collectionId, page } = useParams();
  const [searchKey, setSearchKey] = useState<string>('');
  const [pageSize, setPageSize] = useState<number>(10);
  const [pageNumber, setPageNumber] = useState<number>(1);
  const { modal, message } = App.useApp();
  const { collections, getCollection } = useModel('collection');
  const { documents, documentLoading, totalCount,getDocuments,deleteDocument } = useModel('document');
  const [uploading, setUploading] = useState<boolean>(false);
  const [ collection, setCollection ] = useState<any>();
  const [ readonly, setReadonly ] = useState(false);
  const config = collection?.config;

  useEffect(()=>{
    const collectionDetail = getCollection(collectionId);
    setCollection(collectionDetail);
    setReadonly(collectionDetail?.system && !user?.is_admin);
  }, [collections])

  const dataSource = documents?.filter((c) => {
    return c.name?.match(new RegExp(searchKey, 'i')) || _.isEmpty(searchKey);
  });

  const { formatMessage } = useIntl();

  const getDocument = async (page, page_size) => {
    const pageId = page || pageNumber;
    const page_Size = page_size || pageSize;
    getDocuments(String(collectionId), pageId, page_Size);
    setPageNumber(pageId);
  };

  const changePage = (page, pageSize) => {
    setPageSize(pageSize);
    // getDocument(page, pageSize);
    history.replace(`/collections/${collectionId}/documents/${page}`);
  };

  const onDelete = (record) => {
    if (!collectionId) return;

    let msg = [];

    if(!_.isArray(record)){
      record = [record];
    }

    record.map((item, idx)=>{
      msg.push((idx+1) + '. ' + item.name);
    });

    msg = msg.join('<br/>');

    modal.confirm({
      title: formatMessage({ id: 'text.delete.help' }),
      content: <>{formatMessage({ id: 'text.documents' })}: <div dangerouslySetInnerHTML={{ __html: msg }} /><br/>{formatMessage({ id: 'text.delete.confirm' })}</>,
      onOk: async () => {
        const items = [];
        record.map((item)=>items.push(item.id));
        await deleteDocument(collectionId, items);
        setTimeout(() => {
          getDocument();
        });
      },
      okButtonProps: {
        danger: true,
      },
    });
  };

  const SUPPORTED_DOC_EXTENSIONS=['.pdf','.doc','.docx','.ppt','.pptx','.csv','.xls','.xlsx','.epub','.md','.mbox','.ipynb','.txt','.htm','.html'];
  const SUPPORTED_MEDIA_EXTENSIONS=['.jpg','.jpeg','.png','.webm','.mp3','.mp4','.mpeg','.mpga','.m4a','.wav'];
  const SUPPORTED_COMPRESSED_EXTENSIONS=['.zip','.rar', '.r00','.7z','.tar', '.gz', '.xz', '.bz2', '.tar.gz', '.tar.xz', '.tar.bz2', '.tar.7z'];

  const uploadProps: UploadProps = {
    name: 'file',
    multiple: true,
    disabled: readonly,
    action: `/api/v1/collections/${collectionId}/documents`,
    data: {},
    showUploadList: false,
    headers: {
      Authorization: 'Bearer ' + user?.__raw,
    },
    accept: SUPPORTED_DOC_EXTENSIONS.concat(SUPPORTED_MEDIA_EXTENSIONS).concat(SUPPORTED_COMPRESSED_EXTENSIONS).join(','),
    onChange(info) {
      const { status, response } = info.file;
      if (status === 'done') {
        if (response.code === '200') {
          getDocument();
        } else {
          message.error(response.message || 'update error');
        }
        setUploading(false);
      } else {
        setUploading(true);
        if (status === 'error') {
          message.error('upload error');
        }
      }
    },
  };

  useEffect(() => {
    getDocument(parseInt(page));
  }, [history.location.pathname]);

  return (
    <div className="border-block document">
      <Card bordered={false}>
        <div className='hd'>
          <div className='title'>

          </div>
          <div className="action">
            <label className="search">
              <input
                type="text"
                onChange={(e) => setSearchKey(e.currentTarget.value)}
              />
            </label>
            {!readonly && config?.source === 'system' ? (
                <Upload {...uploadProps} disabled={(readonly || uploading)}>
                  {/* eslint-disable-next-line react/button-has-type */}
                  <button disabled={readonly} className={uploading ? 'waiting' : ''}>
                    <FormattedMessage id="action.documents.add" />
                  </button>
                </Upload>
            ) : null}
            {config?.source === 'url' ? (
              <AddUrl onSuccess={() => getDocument()} collection={collection} />
          ) : null}
          </div>
        </div>
        <div className='bd'>
          <Documentlist list={dataSource} getDocuments={()=> getDocument()} onDelete={onDelete} loading={documentLoading} selection={!readonly && totalCount} editable={!readonly}/>
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
      </Card>
    </div>
  );
};
