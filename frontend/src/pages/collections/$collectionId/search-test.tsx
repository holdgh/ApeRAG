import { SearchTestRequest, SearchTestResult } from '@/api';
import { ApeMarkdown } from '@/components';
import { DATETIME_FORMAT } from '@/constants';
import { api } from '@/services';
import { CaretRightOutlined, DeleteOutlined } from '@ant-design/icons';
import {
  Button,
  Card,
  Collapse,
  Divider,
  Drawer,
  Form,
  Input,
  Popconfirm,
  Progress,
  Result,
  Select,
  Slider,
  Space,
  Table,
  TableProps,
  theme,
  Tooltip,
  Typography,
} from 'antd';
import _ from 'lodash';
import moment from 'moment';
import { useEffect, useState } from 'react';
import { toast } from 'react-toastify';
import { UndrawScience } from 'react-undraw-illustrations';
import { FormattedMessage, useIntl, useModel, useParams } from 'umi';

export default () => {
  const { formatMessage } = useIntl();
  const [form] = Form.useForm<SearchTestRequest>();
  const { collectionId } = useParams();
  const { loading, setLoading } = useModel('global');

  const searchType = Form.useWatch('search_type', form);
  const [records, setRecords] = useState<SearchTestResult[]>([]);
  const [historyModal, setHistoryModal] = useState<{
    visible: boolean;
    record: SearchTestResult | undefined;
  }>();
  const { token } = theme.useToken();

  const fetchHistory = async () => {
    if (!collectionId) return;
    const res = await api.collectionsCollectionIdSearchTestsGet({
      collectionId,
    });
    setRecords(res?.data?.items || []);
  };

  const onSearch = async () => {
    if (!collectionId) return;
    const values = await form.validateFields();
    setLoading(true);
    const res = await api.collectionsCollectionIdSearchTestsPost({
      collectionId,
      searchTestRequest: values,
    });
    setLoading(false);
    if (!res.data) {
      toast.error(formatMessage({ id: 'searchTest.searchFailed' }));
      return;
    }
    setHistoryModal({ visible: true, record: res.data });
    fetchHistory();
  };

  const handleDeleteHistory = async (searchTestId: string) => {
    console.log('delete', searchTestId, collectionId);
    if (!collectionId || !searchTestId) return;
    try {
      await api.collectionsCollectionIdSearchTestsSearchTestIdDelete({
        collectionId,
        searchTestId,
      });
      toast.success(formatMessage({ id: 'searchTest.deleteSuccess' }));
      fetchHistory();
    } catch (e: any) {
      toast.error(
        e?.message || formatMessage({ id: 'searchTest.deleteFailed' }),
      );
    }
  };

  const columns: TableProps<SearchTestResult>['columns'] = [
    {
      title: formatMessage({ id: 'searchTest.question' }),
      dataIndex: 'query',
      render: (_value, record) => {
        return (
          <>
            <Button
              onClick={() => setHistoryModal({ visible: true, record })}
              type="link"
              style={{ padding: 0 }}
            >
              {record.query}
            </Button>
            <div style={{ fontSize: 12, color: token.colorTextSecondary }}>
              <Space split={<Divider type="vertical" />}>
                <div>
                  {formatMessage({
                    id: `searchTest.type.${record.search_type}`,
                  })}
                </div>
                {record.created
                  ? moment(record.created).format(DATETIME_FORMAT)
                  : ''}
              </Space>
            </div>
          </>
        );
      },
    },
    {
      title: formatMessage({ id: 'searchTest.searchResults' }),
      align: 'center',
      render: (text, record) => (
        <Button
          onClick={() => setHistoryModal({ visible: true, record })}
          type="link"
          style={{ padding: 0 }}
        >
          {_.size(record.items)}
        </Button>
      ),
    },
    {
      title: formatMessage({ id: 'searchTest.vectorTopK' }),
      width: 130,
      render: (text, record) => {
        return (
          <Tooltip title={record.vector_search?.topk}>
            <Progress
              style={{ margin: 0, padding: 0, height: 4, lineHeight: 0 }}
              steps={20}
              percent={((record.vector_search?.topk || 0) * 100) / 20}
              size={[3, 4]}
              showInfo={false}
            />
          </Tooltip>
        );
      },
    },
    {
      title: formatMessage({ id: 'searchTest.vectorSimilarity' }),
      width: 130,
      render: (text, record) => {
        return (
          <Tooltip title={record.vector_search?.similarity}>
            <Progress
              steps={20}
              percent={((record.vector_search?.similarity || 0) * 100) / 1}
              size={[3, 4]}
              showInfo={false}
            />
          </Tooltip>
        );
      },
    },
    {
      title: formatMessage({ id: 'searchTest.fulltextTopK' }),
      width: 130,
      render: (text, record) => {
        return (
          <Tooltip title={record.fulltext_search?.topk}>
            <Progress
              steps={20}
              percent={((record.fulltext_search?.topk || 0) * 100) / 20}
              size={[3, 4]}
              showInfo={false}
            />
          </Tooltip>
        );
      },
    },
    {
      title: formatMessage({ id: 'action.name' }),
      key: 'action',
      width: 80,
      align: 'center',
      render: (_: any, record: any) => (
        <Space size={8} wrap={false}>
          <Popconfirm
            title={formatMessage({ id: 'searchTest.confirmDeleteHistory' })}
            onConfirm={() => handleDeleteHistory(record.id)}
            okText={formatMessage({ id: 'action.delete' })}
            cancelText={formatMessage({ id: 'searchTest.cancel' })}
          >
            <Button size="small" type="link" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  useEffect(() => {
    fetchHistory();
  }, [collectionId]);

  useEffect(() => {
    form.setFieldsValue({
      query: '',
      search_type: 'vector',
      vector_search: {
        topk: 5,
        similarity: 0.7,
      },
      fulltext_search: {
        topk: 5,
      },
    });
  }, []);

  return (
    <>
      <Card style={{ marginBottom: 24 }}>
        <Form form={form} onFinish={onSearch}>
          <Form.Item
            name="query"
            required
            style={{ display: 'block' }}
            rules={[
              {
                required: true,
                message: formatMessage({
                  id: 'searchTest.pleaseInputQuestion',
                }),
              },
            ]}
          >
            <Input.TextArea
              placeholder={formatMessage({
                id: 'searchTest.pleaseInputQuestion',
              })}
              rows={3}
            />
          </Form.Item>
        </Form>
        <Space style={{ display: 'flex', justifyContent: 'space-between' }}>
          <Form form={form} layout="inline">
            <Form.Item name="search_type">
              <Select
                style={{
                  width: 140,
                }}
                options={[
                  {
                    label: formatMessage({ id: 'searchTest.type.vector' }),
                    value: 'vector',
                  },
                  {
                    label: formatMessage({ id: 'searchTest.type.fulltext' }),
                    value: 'fulltext',
                  },
                  {
                    label: formatMessage({ id: 'searchTest.type.hybrid' }),
                    value: 'hybrid',
                  },
                ]}
              />
            </Form.Item>
            {_.includes(['vector', 'hybrid'], searchType) && (
              <>
                <Form.Item
                  label={formatMessage({ id: 'searchTest.vectorTopK' })}
                  name={['vector_search', 'topk']}
                >
                  <Slider style={{ width: 80 }} min={0} max={20} />
                </Form.Item>

                <Form.Item
                  label={formatMessage({
                    id: 'searchTest.similarityThreshold',
                  })}
                  name={['vector_search', 'similarity']}
                >
                  <Slider style={{ width: 80 }} min={0} max={1} step={0.01} />
                </Form.Item>
              </>
            )}

            {_.includes(['fulltext', 'hybrid'], searchType) && (
              <>
                <Form.Item
                  label={formatMessage({ id: 'searchTest.fulltextTopK' })}
                  name={['fulltext_search', 'topk']}
                >
                  <Slider style={{ width: 80 }} min={0} max={20} />
                </Form.Item>
              </>
            )}
          </Form>
          <Button loading={loading} onClick={onSearch} type="primary">
            {formatMessage({ id: 'searchTest.test' })}
          </Button>
        </Space>
      </Card>

      <Table dataSource={records} bordered columns={columns} rowKey="id" />

      <Drawer
        open={historyModal?.visible}
        title={formatMessage({ id: 'searchTest.searchResults' })}
        onClose={() => setHistoryModal({ visible: false, record: undefined })}
        footer={false}
        size="large"
        styles={{
          body: {
            padding: 0,
          },
        }}
        width="60%"
      >
        {_.size(historyModal?.record?.items) ? (
          <Collapse
            bordered={false}
            defaultActiveKey={['1', '2', '3']}
            expandIcon={({ isActive }) => (
              <CaretRightOutlined rotate={isActive ? 90 : 0} />
            )}
            style={{ background: token.colorBgContainer }}
            items={historyModal?.record?.items?.map((item) => ({
              key: item.rank,
              label: (
                <Typography.Text
                  style={{ maxWidth: 400, color: token.colorPrimary }}
                  ellipsis
                >
                  {item.rank}. {item.source}
                </Typography.Text>
              ),
              children: <ApeMarkdown>{item.content}</ApeMarkdown>,
              extra: (
                <Tooltip title={item.score}>
                  <Space align="center">
                    <Progress
                      type="circle"
                      percent={((item.score || 0) * 100) / 1}
                      showInfo={false}
                      size={20}
                      strokeColor={{
                        '0%': token.colorError,
                        '25%': token.colorWarning,
                        '50%': token.colorSuccess,
                      }}
                    />
                    <Typography.Text type="secondary">
                      {(item.score || 0).toFixed(2)}
                    </Typography.Text>
                  </Space>
                </Tooltip>
              ),
            }))}
          />
        ) : (
          <Result
            style={{ paddingTop: 120 }}
            icon={
              <UndrawScience primaryColor={token.colorPrimary} height="200px" />
            }
            subTitle={<FormattedMessage id="searchTest.searchResults.empty" />}
          />
        )}
      </Drawer>
    </>
  );
};
