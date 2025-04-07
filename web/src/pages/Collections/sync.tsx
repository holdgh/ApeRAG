import { DOCUMENT_DEFAULT_CONFIG } from '@/constants';
import {
  CancelSyncCollection,
  GetCollectionSyncHistories,
  SyncCollection,
} from '@/services/collections';
import { TypesCollectionSyncHistory } from '@/types';
import { FieldTimeOutlined } from '@ant-design/icons';
import { FormattedMessage, getLocale, useModel, useParams } from '@umijs/max';
import {
  Button,
  Card,
  Divider,
  Progress,
  Space,
  Switch,
  Table,
  Typography,
} from 'antd';
import { ColumnsType } from 'antd/es/table';
import _ from 'lodash';
import moment from 'moment';
import { useEffect, useState } from 'react';
import { Cron } from 'react-js-cron';

import { EN_US, ZH_CN } from '@/utils/cron_locale';

export default () => {
  const [syncHistories, setSyncHistories] = useState<TypesCollectionSyncHistory[]>([]);
  const { collectionId } = useParams();
  const { collections, getCollection, updateCollection } = useModel('collection');
  const [collection, setCollection] = useState();
  const getCurrentCollenction = () => {
    setCollection(getCollection(collectionId));
  }
  const [syncHistoriesLoading, setSyncHistoriesLoading] = useState<boolean>(false);
  const [value, setValue] = useState<string>('');

  const [enabledSchedule, setEnabledSchedule] = useState<boolean>(
    collection?.config?.crontab?.enabled || false,
  );

  const locale = getLocale();

  const getSyncHistories = async () => {
    if (!collectionId) return;
    setSyncHistoriesLoading(true);
    const res = await GetCollectionSyncHistories(collectionId);
    setSyncHistoriesLoading(false);
    setSyncHistories(res.data || []);
  };

  const executeSync = async () => {
    if (!collectionId) return;
    const { code } = await SyncCollection(collectionId);
    if (code === '200') {
      getSyncHistories();
    }
  };

  const executeCancelSync = async (syncId: string) => {
    if (!collectionId || !syncId) return;
    await CancelSyncCollection(collectionId, syncId);
    getSyncHistories();
  };

  const onUpdateSchedule = async () => {
    if (!collection?.id || !value) return;
    const [minute, hour, day_of_month, month, day_of_week] = value.split(' ');
    const contab = {
      minute,
      hour,
      day_of_month,
      month,
      day_of_week,
    };
    _.set(collection, 'config.crontab', contab);
    _.set(collection, 'config.crontab.enabled', enabledSchedule);
    updateCollection(collection.id, collection);
  };

  useEffect(() => {

    getCurrentCollenction();

    if(!collections){return;}

    getSyncHistories();

    const crontab = collection?.config?.crontab || DOCUMENT_DEFAULT_CONFIG.crontab;
    
    if (!crontab) return;

    setEnabledSchedule(crontab.enabled);

    const { minute, hour, day_of_month, month, day_of_week } = crontab;
    setValue(`${minute} ${hour} ${day_of_month} ${month} ${day_of_week}`);
  }, [collections]);

  useEffect(()=>{
    let allStatusReady = true;
    if(syncHistories){
      syncHistories.map((item)=>{
        if(item.status==='RUNNING'){
          allStatusReady = false;
        }
      });
    }

    const timer = setTimeout(()=>{
      if(allStatusReady){return;}
      getSyncHistories();
    }, 2000);

    return () => {
      clearTimeout(timer);  
    };
  },[syncHistories])

  const columns: ColumnsType<TypesCollectionSyncHistory> = [
    {
      title: 'ID',
      dataIndex: 'id',
      render: (value, record) => (
        <Space direction="vertical">
          <Typography.Text>{value}</Typography.Text>
        </Space>
      ),
    },
    {
      width: 100,
      className: 'sync-at',
      title: <FormattedMessage id="text.started" />,
      render: (value, record) => (
        <Typography.Text>{moment(record.start_time).fromNow()}</Typography.Text>
      ),
    },
    {
      width: 80,
      title: <FormattedMessage id="text.documents" />,
      onCell: (record, index)=>({
        colSpan: record.status!=='RUNNING' ? 2 : 1,
      }),
      render: (value, record) => {
        let status;
        switch (record.status) {
          case 'RUNNING':
            let percentage = _.round(
              record.total_documents_to_sync === 0
                ? record.status==='RUNNING' ? 99 : 100
                : ((record.failed_documents + record.successful_documents) *
                    100) /
                    record.total_documents_to_sync,
              2,
            );
            status = <>
              <Progress
                status='active'
                style={{ margin: 0 }}
                showInfo={false}
                percent={percentage}
              />
              <br/>
              <Typography.Text type="secondary" style={{fontSize:'0.8rem'}}>
                {percentage}%
              </Typography.Text>
              </>;
            break;
          default:
            status = <Typography.Text type="secondary">{record.total_documents_to_sync}</Typography.Text>;
        }
        return status;
      },
    },
    {
      width: 50,
      onCell: (record, index)=>({
        colSpan: record.status!=='RUNNING' ? 0 : 1,
      }),
      render: (value, record) => {
        return (
          <Space>
            {record.status === 'RUNNING' ? (
              <Button
                style={{ fontSize: 12 }}
                type="link"
                onClick={() => executeCancelSync(record.id)}
              >
                <FormattedMessage id="action.cancel" />
              </Button>
            ) : null}
          </Space>
        );
      },
    },
  ];

  if (!collection) return null;

  return (
    <div className="border-block sync">
      <Card bordered={false} style={{ marginBottom: 20 }}>
        <Space style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Space style={{ alignItems: 'flex-start' }}>
            <FieldTimeOutlined style={{ fontSize: 60, opacity: 0.2 }} />
            <div>
              <Typography.Paragraph strong>
                <FormattedMessage id="text.sync_schedule" />
                &nbsp;
                <Switch
                  checked={enabledSchedule}
                  onChange={setEnabledSchedule}
                />
              </Typography.Paragraph>
              <div>
                {enabledSchedule ? (
                  <Cron
                    value={value}
                    setValue={setValue}
                    clearButton={false}
                    defaultPeriod="day"
                    mode="single"
                    locale={locale === 'en-US' ? EN_US : ZH_CN}
                    allowedPeriods={[
                      'month',
                      'week',
                      'day',
                      'hour',
                      'minute',
                    ]}
                    allowedDropdowns={[
                      'period',
                      'months',
                      // 'month-days',
                      'week-days',
                      'hours',
                      'minutes',
                    ]}
                  />
                ) : (
                  <Typography.Text type="secondary">
                    <FormattedMessage id="text.schedule_help" />
                  </Typography.Text>
                )}
              </div>
            </div>
          </Space>
          <div>
            {/* eslint-disable-next-line react/button-has-type */}
            <Button onClick={onUpdateSchedule}>
              <FormattedMessage id="text.schedule_save" />
            </Button>
          </div>
        </Space>
      </Card>
      <Card
        title={<FormattedMessage id="text.sync_history" />}
        extra={
          <Space split={<Divider type="vertical" />}>
            {/* eslint-disable-next-line react/button-has-type */}
            <button
              onClick={() => {
                executeSync();
              }}
            >
              <FormattedMessage id="text.sync_now" />
            </button>
            
          </Space>
        }
        bordered={false}
      >
        <Table
          className='sync-list'
          rowKey="id"
          columns={columns}
          dataSource={syncHistories.reverse()}
          loading={syncHistoriesLoading}
          pagination={{ position: ['bottomCenter'] }}
          expandable={{
            expandedRowRender: (record) => <Card title={<><FormattedMessage id="text.started" />&nbsp;{moment(record.start_time).format('YYYY-MM-DD HH:MM:SS')}</>}>
            <Space size="small" style={{display:'grid',gridTemplateColumns:'repeat(3, 1fr)'}}>
            <Typography.Text type="secondary">
              <FormattedMessage id="text.new" />: 
              {record.new_documents}
            </Typography.Text>
            <Typography.Text type="secondary">
              <FormattedMessage id="text.removed" />: 
              {record.deleted_documents}
            </Typography.Text>
            <Typography.Text type="secondary">
              <FormattedMessage id="text.modified" />: 
              {record.modified_documents}
            </Typography.Text>
            </Space>
            <Space size="small" style={{display:'grid',gridTemplateColumns:'repeat(3, 1fr)',marginTop:'1rem'}}>
            <Typography.Text type={record.failed_documents ? 'danger' : 'secondary'}>
              <FormattedMessage id="text.failed" />: 
              {record.failed_documents}
            </Typography.Text>
            <Typography.Text type={record.successful_documents ? 'success' : 'secondary'}>
              <FormattedMessage id="text.succeess" />: 
              {record.successful_documents}
            </Typography.Text>
            <Typography.Text type={record.processing_documents ? 'warning' : 'secondary'}>
              <FormattedMessage id="text.processing" />: 
              {record.processing_documents}
            </Typography.Text>
            </Space>
            </Card>
          }}
        />
      </Card>
    </div>
  );
};
