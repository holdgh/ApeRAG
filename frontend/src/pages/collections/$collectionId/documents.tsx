import {
  DocumentFulltextIndexStatusEnum,
  DocumentGraphIndexStatusEnum,
  DocumentVectorIndexStatusEnum,
} from '@/api';
import { RefreshButton } from '@/components';
import {
  DATETIME_FORMAT,
  SUPPORTED_COMPRESSED_EXTENSIONS,
  SUPPORTED_DOC_EXTENSIONS,
  SUPPORTED_MEDIA_EXTENSIONS,
  UI_DOCUMENT_STATUS,
  UI_INDEX_STATUS,
} from '@/constants';
import { getAuthorizationHeader } from '@/models/user';
import { api } from '@/services';
import { ApeDocument } from '@/types';
import { parseConfig } from '@/utils';
import {
  DeleteOutlined,
  MoreOutlined,
  SearchOutlined,
  DatabaseOutlined,
} from '@ant-design/icons';
import { useRequest } from 'ahooks';
import {
  Avatar,
  Badge,
  Button,
  Dropdown,
  Input,
  Modal,
  Space,
  Table,
  TableProps,
  theme,
  Typography,
  Upload,
  UploadProps,
  Drawer,
  List,
  Card,
  Divider,
  Empty,
  Spin,
  Tag,
  Tooltip,
} from 'antd';
import byteSize from 'byte-size';
import alpha from 'color-alpha';
import _ from 'lodash';
import moment from 'moment';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { defaultStyles, FileIcon } from 'react-file-icon';
import { toast } from 'react-toastify';
import { FormattedMessage, useIntl, useModel, useParams } from 'umi';

export default () => {
  const [searchParams, setSearchParams] = useState<{
    name?: string;
  }>();
  const { collectionId } = useParams();
  const { collection } = useModel('collection');
  const { setLoading } = useModel('global');
  const { token } = theme.useToken();
  const [modal, contextHolder] = Modal.useModal();
  const { formatMessage } = useIntl();
  const {
    data: documentsRes,
    run: getDocuments,
    loading: documentsLoading,
  } = useRequest(
    () =>
      api.collectionsCollectionIdDocumentsGet({
        collectionId: collectionId || '',
      }),
    {
      refreshDeps: [collectionId],
      pollingInterval: 3000,
    },
  );
  const [vectorIndexDrawer, setVectorIndexDrawer] = useState<{
    visible: boolean;
    document?: ApeDocument;
  }>({ visible: false });

  const {
    data: vectorIndexData,
    run: fetchVectorIndex,
    loading: vectorIndexLoading,
  } = useRequest(
    (collectionId: string, documentId: string) =>
      api.collectionsCollectionIdDocumentsDocumentIdVectorIndexGet({
        collectionId,
        documentId,
      }),
    {
      manual: true,
    },
  );

  const deleteDocument = useCallback(
    async (documentId?: string) => {
      if (!collectionId || !documentId) return;
      const res = await api.collectionsCollectionIdDocumentsDocumentIdDelete({
        collectionId,
        documentId,
      });
      if (res) {
        toast.success(formatMessage({ id: 'tips.delete.success' }));
        getDocuments();
      }
    },
    [collectionId],
  );

  const renderIndexStatus = (
    vectorStatus?: DocumentVectorIndexStatusEnum,
    fulltextStatus?: DocumentFulltextIndexStatusEnum,
    graphStatus?: DocumentGraphIndexStatusEnum,
  ) => {
    const indexTypes = [
      { nameKey: 'document.index.type.vector', status: vectorStatus },
      { nameKey: 'document.index.type.fulltext', status: fulltextStatus },
      { nameKey: 'document.index.type.graph', status: graphStatus },
    ];
    return (
      <Space direction="vertical" size="small">
        {indexTypes.map(({ nameKey, status }, index) => (
          <div 
            key={index} 
            style={{ 
              fontSize: '12px', 
              lineHeight: '18px',
              display: 'flex',
              alignItems: 'center',
              whiteSpace: 'nowrap'
            }}
          >
            <span 
              style={{ 
                color: '#666',
                width: '100px',
                textAlign: 'right',
                display: 'inline-block'
              }}
            >
              {formatMessage({ id: nameKey })}
            </span>
            <span 
              style={{ 
                color: '#666',
                width: '12px',
                textAlign: 'center',
                display: 'inline-block'
              }}
            >
              ：
            </span>
            <div style={{ width: '80px' }}>
              <Badge
                status={UI_INDEX_STATUS[status as keyof typeof UI_INDEX_STATUS]}
                text={
                  <span style={{ display: 'inline-block', width: '70px' }}>
                    {formatMessage({ id: `document.index.status.${status}` })}
                  </span>
                }
              />
            </div>
          </div>
        ))}
      </Space>
    );
  };

  const openVectorIndexDrawer = useCallback(
    (document: ApeDocument) => {
      setVectorIndexDrawer({ visible: true, document });
      if (collectionId && document.id) {
        fetchVectorIndex(collectionId, document.id);
      }
    },
    [collectionId, fetchVectorIndex],
  );

  const closeVectorIndexDrawer = useCallback(() => {
    setVectorIndexDrawer({ visible: false });
  }, []);

  const columns: TableProps<ApeDocument>['columns'] = [
    {
      title: formatMessage({ id: 'document.name' }),
      dataIndex: 'name',
      render: (value, record) => {
        const extension =
          record.name?.split('.').pop()?.toLowerCase() ||
          ('unknow' as keyof typeof defaultStyles);
        const iconProps = _.get(defaultStyles, extension);
        const icon = (
          // @ts-ignore
          <FileIcon
            color={alpha(token.colorPrimary, 0.8)}
            extension={extension}
            {...iconProps}
          />
        );

        return (
          <Space>
            <Avatar size={36} shape="square" src={icon} />
            <div>
              <div>{record.name}</div>
              <Typography.Text type="secondary">
                {byteSize(record.size || 0).toString()}
              </Typography.Text>
            </div>
          </Space>
        );
      },
    },
    {
      title: formatMessage({ id: 'document.status' }),
      dataIndex: 'status',
      width: 190,
      align: 'center',
      render: (value, record) => {
        return renderIndexStatus(
          record.vector_index_status,
          record.fulltext_index_status,
          record.graph_index_status,
        );
      },
    },
    {
      title: formatMessage({ id: 'text.updatedAt' }),
      dataIndex: 'updated',
      width: 180,
      render: (value) => {
        return moment(value).format(DATETIME_FORMAT);
      },
    },
    {
      title: formatMessage({ id: 'action.name' }),
      width: 80,
      render: (value, record) => {
        return (
          <Dropdown
            trigger={['click']}
            menu={{
              items: [
                {
                  key: 'vector-index-details',
                  label: formatMessage({ id: 'document.vector.index.details' }),
                  icon: <DatabaseOutlined />,
                  disabled: record.vector_index_status !== 'COMPLETE',
                  onClick: () => openVectorIndexDrawer(record),
                },
                {
                  key: 'delete',
                  label: formatMessage({ id: 'action.delete' }),
                  danger: true,
                  icon: <DeleteOutlined />,
                  disabled: record.status === 'DELETING',
                  onClick: async () => {
                    const confirmed = await modal.confirm({
                      title: formatMessage({ id: 'action.confirm' }),
                      content: formatMessage(
                        { id: 'document.delete.confirm' },
                        { name: record.name },
                      ),
                      okButtonProps: {
                        danger: true,
                      },
                    });
                    if (confirmed) {
                      deleteDocument(record.id);
                    }
                  },
                },
              ],
            }}
            overlayStyle={{ width: 200 }}
          >
            <Button type="text" icon={<MoreOutlined />} />
          </Dropdown>
        );
      },
    },
  ];

  const uploadProps = useMemo(
    (): UploadProps => ({
      name: 'files',
      multiple: true,
      // disabled: readonly,
      action: `/api/v1/collections/${collectionId}/documents`,
      data: {},
      showUploadList: false,
      headers: {
        ...getAuthorizationHeader(),
      },
      accept: SUPPORTED_DOC_EXTENSIONS.concat(SUPPORTED_MEDIA_EXTENSIONS)
        .concat(SUPPORTED_COMPRESSED_EXTENSIONS)
        .join(','),
      onChange(info) {
        const { status } = info.file; // todo
        if (status === 'done') {
          if (collectionId) {
            getDocuments();
          }
          setLoading(false);
        } else {
          setLoading(true);
          if (status === 'error') {
            toast.error(formatMessage({ id: 'tips.upload.error' }));
          }
        }
      },
    }),
    [collectionId],
  );

  const documents = useMemo(
    () =>
      documentsRes?.data.items
        ?.map((document) => {
          const item: ApeDocument = {
            ...document,
            config: parseConfig(document.config),
          };
          return item;
        })
        .filter((item) => {
          const titleMatch = searchParams?.name
            ? item.name?.includes(searchParams.name)
            : true;
          return titleMatch;
        }),
    [documentsRes, searchParams],
  );

  useEffect(() => setLoading(documentsLoading), [documentsLoading]);

  return (
    <>
      <Space
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          marginBottom: 24,
        }}
      >
        <Input
          placeholder={formatMessage({ id: 'action.search' })}
          prefix={
            <Typography.Text disabled>
              <SearchOutlined />
            </Typography.Text>
          }
          onChange={(e) => {
            setSearchParams({ ...searchParams, name: e.currentTarget.value });
          }}
          allowClear
          value={searchParams?.name}
        />
        <Space>
          {collection?.config?.source === 'system' ? (
            <Upload {...uploadProps}>
              <Button type="primary">
                <FormattedMessage id="document.upload" />
              </Button>
            </Upload>
          ) : null}
          <RefreshButton
            loading={documentsLoading}
            onClick={() => collectionId && getDocuments()}
          />
        </Space>
      </Space>
      <Table rowKey="id" bordered columns={columns} dataSource={documents} />
      {contextHolder}
      
      <Drawer
        title={
          <Space>
            <DatabaseOutlined />
            <span>{formatMessage({ id: 'document.vector.index.title' })}</span>
            {vectorIndexDrawer.document && (
              <Typography.Text type="secondary">
                - {vectorIndexDrawer.document.name}
              </Typography.Text>
            )}
          </Space>
        }
        placement="right"
        size="large"
        open={vectorIndexDrawer.visible}
        onClose={closeVectorIndexDrawer}
        extra={
          <Space>
            {vectorIndexData?.data && (
              <Tag color="blue">
                {formatMessage({ id: 'document.vector.index.count' })}: {vectorIndexData.data.vector_count || 0}
              </Tag>
            )}
          </Space>
        }
      >
        {vectorIndexLoading ? (
          <div style={{ textAlign: 'center', padding: '50px 0' }}>
            <Spin size="large" />
            <Typography.Text style={{ display: 'block', marginTop: 16 }}>
              {formatMessage({ id: 'document.vector.index.loading' })}
            </Typography.Text>
          </div>
        ) : vectorIndexData?.data?.vectors && vectorIndexData.data.vectors.length > 0 ? (
          <List
            dataSource={vectorIndexData.data.vectors}
            renderItem={(vector, index) => (
              <List.Item key={vector.id}>
                <Card
                  size="small"
                  style={{ width: '100%' }}
                  title={
                    <Space>
                      <Typography.Text strong>
                        {formatMessage({ id: 'document.vector.index.id' })}: {vector.id}
                      </Typography.Text>
                      {vector.chunk_order_index !== undefined && (
                        <Tag color="geekblue">
                          #{vector.chunk_order_index + 1}
                        </Tag>
                      )}
                    </Space>
                  }
                  extra={
                    <Space>
                      {vector.tokens && (
                        <Tooltip title={formatMessage({ id: 'document.vector.index.tokens' })}>
                          <Tag color="orange">{vector.tokens} tokens</Tag>
                        </Tooltip>
                      )}
                      {vector.created_at && (
                        <Typography.Text type="secondary" style={{ fontSize: '12px' }}>
                          {moment(vector.created_at * 1000).format(DATETIME_FORMAT)}
                        </Typography.Text>
                      )}
                    </Space>
                  }
                  bodyStyle={{ padding: '12px' }}
                >
                  <Typography.Paragraph
                    ellipsis={{ rows: 3, expandable: true, symbol: 'more' }}
                    style={{ margin: 0, fontSize: '13px', lineHeight: '1.5' }}
                  >
                    {vector.content || 'No content available'}
                  </Typography.Paragraph>
                </Card>
              </List.Item>
            )}
          />
        ) : (
          <Empty
            description={formatMessage({ id: 'document.vector.index.empty' })}
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        )}
      </Drawer>
    </>
  );
};
