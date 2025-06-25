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
  ReloadOutlined,
  FileTextOutlined,
  SplitCellsOutlined,
  CaretRightOutlined,
} from '@ant-design/icons';
import { useRequest } from 'ahooks';
import {
  Avatar,
  Badge,
  Button,
  Checkbox,
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
  Tooltip,
  Drawer,
  Row,
  Col,
  Card,
  Spin,
  Alert,
  Divider,
  Tag,
  Collapse,
} from 'antd';
import byteSize from 'byte-size';
import alpha from 'color-alpha';
import _ from 'lodash';
import moment from 'moment';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { defaultStyles, FileIcon } from 'react-file-icon';
import { toast } from 'react-toastify';
import { FormattedMessage, useIntl, useModel, useParams } from 'umi';
import { getDocumentContent, getDocumentChunks } from '@/api/document-api';

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
  const [rebuildModalVisible, setRebuildModalVisible] = useState(false);
  const [rebuildSelectedDocument, setRebuildSelectedDocument] = useState<ApeDocument | null>(null);
  const [rebuildSelectedTypes, setRebuildSelectedTypes] = useState<string[]>([]);
  
  // Document detail drawer state
  const [documentDetailVisible, setDocumentDetailVisible] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState<ApeDocument | null>(null);
  const [documentContent, setDocumentContent] = useState<any>(null);
  const [documentChunks, setDocumentChunks] = useState<any[]>([]);
  const [detailLoading, setDetailLoading] = useState(false);
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

  const handleRebuildIndex = (document: ApeDocument) => {
    setRebuildSelectedDocument(document);
    setRebuildSelectedTypes(['VECTOR', 'FULLTEXT', 'GRAPH']);
    setRebuildModalVisible(true);
  };

  const handleRebuildConfirm = async () => {
    if (!rebuildSelectedDocument || rebuildSelectedTypes.length === 0) return;

    try {
      setLoading(true);
      await api.collectionsCollectionIdDocumentsDocumentIdRebuildIndexesPost({
        collectionId: collectionId!,
        documentId: rebuildSelectedDocument.id!,
        rebuildIndexesRequest: {
          index_types: rebuildSelectedTypes as ('VECTOR' | 'FULLTEXT' | 'GRAPH')[],
        },
      });
      toast.success(formatMessage({ id: 'document.index.rebuild.success' }));
      setRebuildModalVisible(false);
      setRebuildSelectedDocument(null);
      setRebuildSelectedTypes([]);
      getDocuments();
    } catch (error) {
      toast.error(formatMessage({ id: 'document.index.rebuild.failed' }));
    } finally {
      setLoading(false);
    }
  };

  // Handle document detail view
  const handleViewDocumentDetail = async (document: ApeDocument) => {
    if (!collectionId || !document.id) return;

    setSelectedDocument(document);
    setDocumentDetailVisible(true);
    setDetailLoading(true);
    setDocumentContent(null);
    setDocumentChunks([]);

    try {
      // Fetch document content and chunks in parallel
      const [contentResponse, chunksResponse] = await Promise.all([
        getDocumentContent({
          collectionId,
          documentId: document.id,
        }),
        getDocumentChunks({
          collectionId,
          documentId: document.id,
        }),
      ]);

      setDocumentContent(contentResponse.data);
      setDocumentChunks(chunksResponse.data?.chunks || []);
    } catch (error) {
      console.error('Failed to fetch document details:', error);
      toast.error(formatMessage({ id: 'document.detail.fetch.failed' }));
    } finally {
      setDetailLoading(false);
    }
  };

  const handleCloseDocumentDetail = () => {
    setDocumentDetailVisible(false);
    setSelectedDocument(null);
    setDocumentContent(null);
    setDocumentChunks([]);
  };

  const indexTypeOptions = [
    { label: formatMessage({ id: 'document.index.type.vector' }), value: 'VECTOR' },
    { label: formatMessage({ id: 'document.index.type.fulltext' }), value: 'FULLTEXT' },
    { label: formatMessage({ id: 'document.index.type.graph' }), value: 'GRAPH' },
  ];

  const renderIndexStatus = (
    status?: DocumentVectorIndexStatusEnum | DocumentFulltextIndexStatusEnum | DocumentGraphIndexStatusEnum,
    updatedTime?: string
  ) => {
    const statusBadge = (
      <Badge
        status={UI_INDEX_STATUS[status as keyof typeof UI_INDEX_STATUS]}
        text={formatMessage({ id: `document.index.status.${status}` })}
      />
    );

    if (updatedTime) {
      return (
        <Tooltip title={`${formatMessage({ id: 'text.updatedAt' })}: ${moment(updatedTime).format(DATETIME_FORMAT)}`}>
          {statusBadge}
        </Tooltip>
      );
    }

    return statusBadge;
  };

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
              <div>
                <Typography.Link
                  onClick={() => handleViewDocumentDetail(record)}
                  style={{ cursor: 'pointer' }}
                >
                  {record.name}
                </Typography.Link>
              </div>
              <Typography.Text type="secondary">
                {byteSize(record.size || 0).toString()}
              </Typography.Text>
            </div>
          </Space>
        );
      },
    },
    {
      title: formatMessage({ id: 'document.index.type.vector' }),
      dataIndex: 'vector_index_status',
      width: 120,
      align: 'center',
      render: (value, record) => {
        return renderIndexStatus(record.vector_index_status, record.vector_index_updated);
      },
    },
    {
      title: formatMessage({ id: 'document.index.type.fulltext' }),
      dataIndex: 'fulltext_index_status',
      width: 120,
      align: 'center',
      render: (value, record) => {
        return renderIndexStatus(record.fulltext_index_status, record.fulltext_index_updated);
      },
    },
    {
      title: formatMessage({ id: 'document.index.type.graph' }),
      dataIndex: 'graph_index_status',
      width: 120,
      align: 'center',
      render: (value, record) => {
        return renderIndexStatus(record.graph_index_status, record.graph_index_updated);
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
                  key: 'rebuild',
                  label: formatMessage({ id: 'document.index.rebuild' }),
                  icon: <ReloadOutlined />,
                  disabled: record.status === 'DELETING' || record.status === 'DELETED',
                  onClick: () => handleRebuildIndex(record),
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
            overlayStyle={{ width: 160 }}
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
      documentsRes?.data?.items
        ?.map((document: any) => {
          const item: ApeDocument = {
            ...document,
            config: parseConfig(document.config),
          };
          return item;
        })
        .filter((item: ApeDocument) => {
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
      
      <Modal
        title={formatMessage({ id: 'document.index.rebuild.title' })}
        open={rebuildModalVisible}
        onCancel={() => {
          setRebuildModalVisible(false);
          setRebuildSelectedDocument(null);
          setRebuildSelectedTypes([]);
        }}
        onOk={handleRebuildConfirm}
        okText={formatMessage({ id: 'document.index.rebuild.confirm' })}
        cancelText={formatMessage({ id: 'action.cancel' })}
        okButtonProps={{
          disabled: rebuildSelectedTypes.length === 0,
        }}
      >
        <div style={{ marginBottom: 16 }}>
          <Typography.Text type="secondary">
            {formatMessage({ id: 'document.index.rebuild.description' })}
          </Typography.Text>
        </div>
        
        {rebuildSelectedDocument && (
          <div style={{ marginBottom: 16 }}>
            <Typography.Text strong>
              {rebuildSelectedDocument.name}
            </Typography.Text>
          </div>
        )}
        
        <div style={{ marginBottom: 16 }}>
          <Checkbox
            indeterminate={rebuildSelectedTypes.length > 0 && rebuildSelectedTypes.length < indexTypeOptions.length}
            checked={rebuildSelectedTypes.length === indexTypeOptions.length}
            onChange={(e) => {
              if (e.target.checked) {
                setRebuildSelectedTypes(indexTypeOptions.map(option => option.value));
              } else {
                setRebuildSelectedTypes([]);
              }
            }}
          >
            {formatMessage({ id: 'document.index.rebuild.select.all' })}
          </Checkbox>
        </div>
        
        <Checkbox.Group
          options={indexTypeOptions}
          value={rebuildSelectedTypes}
          onChange={(values) => setRebuildSelectedTypes(values as string[])}
          style={{ display: 'flex', flexDirection: 'row', gap: 16 }}
        />
      </Modal>

      {/* Document Detail Drawer */}
      <Drawer
        title={
          <Space>
            <FileTextOutlined />
            {formatMessage({ id: 'document.detail.title' })}
          </Space>
        }
        open={documentDetailVisible}
        onClose={handleCloseDocumentDetail}
        width="80%"
        extra={
          selectedDocument && (
            <Typography.Text type="secondary">
              {selectedDocument.name}
            </Typography.Text>
          )
        }
      >
        {detailLoading ? (
          <div style={{ textAlign: 'center', padding: '60px 0' }}>
            <Spin size="large" />
            <div style={{ marginTop: 16 }}>
              <Typography.Text type="secondary">
                {formatMessage({ id: 'document.detail.loading' })}
              </Typography.Text>
            </div>
          </div>
        ) : (
          <Row gutter={[16, 16]} style={{ height: '100%' }}>
              {/* Left: Original Content */}
              <Col span={12}>
              <Card
                title={
                  <Space>
                    <FileTextOutlined />
                    {formatMessage({ id: 'document.detail.original.content' })}
                  </Space>
                }
                size="small"
                style={{ height: '100%' }}
                bodyStyle={{ height: 'calc(100% - 57px)', overflow: 'auto' }}
              >
                {documentContent ? (
                  <div style={{ whiteSpace: 'pre-wrap', fontSize: '14px', lineHeight: '1.6' }}>
                    {typeof documentContent?.content === 'string' ? documentContent.content : (documentContent?.content ? JSON.stringify(documentContent.content) : formatMessage({ id: 'document.detail.no.content' }))}
                  </div>
                ) : (
                  <Alert
                    message={formatMessage({ id: 'document.detail.content.unavailable' })}
                    type="warning"
                    showIcon
                  />
                )}
              </Card>
            </Col>

            {/* Right: Chunks */}
            <Col span={12}>
              <Card
                title={
                  <Space>
                    <SplitCellsOutlined />
                    {formatMessage({ id: 'document.detail.chunks' })}
                    <Tag color="blue">{documentChunks.length}</Tag>
                  </Space>
                }
                size="small"
                style={{ height: '100%' }}
                bodyStyle={{ height: 'calc(100% - 57px)', overflow: 'auto', padding: 0 }}
              >
                {Array.isArray(documentChunks) && documentChunks.length > 0 ? (
                  <Collapse
                    size="small"
                    expandIcon={({ isActive }) => (
                      <CaretRightOutlined rotate={isActive ? 90 : 0} />
                    )}
                    style={{ border: 'none' }}
                    defaultActiveKey={documentChunks.map((_, index) => index)}
                    items={documentChunks.map((chunk, index) => ({
                      key: chunk?.id || index,
                      label: (
                        <Space>
                          <Typography.Text strong>
                            {formatMessage({ id: 'document.chunk.index' }, { index: index + 1 })}
                          </Typography.Text>
                          {chunk?.id && (
                            <Tag color="blue">
                              ID: {chunk.id}
                            </Tag>
                          )}
                          {chunk?.metadata?.tokens && (
                            <Tag color="green">
                              {formatMessage({ id: 'document.chunk.tokens' }, { count: chunk.metadata.tokens })}
                            </Tag>
                          )}
                        </Space>
                      ),
                      children: (
                        <div style={{ padding: '8px 12px' }}>
                          {/* Metadata Section */}
                          {chunk?.metadata && Object.keys(chunk.metadata).length > 0 && (
                            <>
                              <Typography.Text type="secondary" style={{ fontSize: '12px' }}>
                                {formatMessage({ id: 'document.chunk.metadata' })}:
                              </Typography.Text>
                              <div style={{ marginTop: 4, marginBottom: 12 }}>
                                {Object.entries(chunk?.metadata || {}).map(([key, value]) => (
                                  <Tag key={key} style={{ marginBottom: 4 }}>
                                    {key}: {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                                  </Tag>
                                ))}
                              </div>
                            </>
                          )}
                          
                          {/* Vector Data Section */}
                          {chunk?.vector && Array.isArray(chunk.vector) && chunk.vector.length > 0 && (
                            <>
                              <Typography.Text type="secondary" style={{ fontSize: '12px' }}>
                                向量数据 (维度: {chunk.vector.length}):
                              </Typography.Text>
                              <div style={{ marginTop: 4, marginBottom: 12 }}>
                                <div style={{ 
                                  fontSize: '11px',
                                  backgroundColor: '#f8f9fa',
                                  padding: '8px',
                                  borderRadius: '4px',
                                  border: '1px solid #e9ecef'
                                }}>
                                  <Typography.Text style={{ fontSize: '11px', color: '#666' }}>
                                    前10维: [{chunk.vector.slice(0, 10).map((v: any) => Number(v).toFixed(4)).join(', ')}
                                    {chunk.vector.length > 10 ? ', ...' : ''}]
                                  </Typography.Text>
                                  {chunk.vector.length > 10 && (
                                    <Collapse
                                      size="small"
                                      ghost
                                      style={{ marginTop: 8 }}
                                      items={[
                                        {
                                          key: 'full-vector',
                                          label: (
                                            <Typography.Text style={{ fontSize: '11px', color: '#1890ff' }}>
                                              查看完整向量 ({chunk.vector.length} 维)
                                            </Typography.Text>
                                          ),
                                          children: (
                                            <div style={{ 
                                              maxHeight: '150px', 
                                              overflow: 'auto',
                                              fontSize: '10px',
                                              fontFamily: 'monospace',
                                              backgroundColor: '#ffffff',
                                              padding: '8px',
                                              borderRadius: '4px',
                                              border: '1px solid #d9d9d9',
                                              lineHeight: '1.4'
                                            }}>
                                              [{chunk.vector.map((v: any) => Number(v).toFixed(4)).join(', ')}]
                                            </div>
                                          )
                                        }
                                      ]}
                                    />
                                  )}
                                </div>
                              </div>
                            </>
                          )}
                          
                          {/* Content Section */}
                          <Typography.Text type="secondary" style={{ fontSize: '12px' }}>
                            {formatMessage({ id: 'document.chunk.content' })}:
                          </Typography.Text>
                          <div style={{ 
                            whiteSpace: 'pre-wrap', 
                            fontSize: '13px', 
                            lineHeight: '1.5',
                            backgroundColor: token.colorBgContainer,
                            border: `1px solid ${token.colorBorder}`,
                            borderRadius: '6px',
                            padding: '12px',
                            marginTop: '4px'
                          }}>
                            {typeof chunk?.content === 'string' ? chunk.content : (chunk?.content ? JSON.stringify(chunk.content) : formatMessage({ id: 'document.chunk.no.content' }))}
                          </div>
                        </div>
                      ),
                    }))}
                  />
                ) : (
                  <div style={{ padding: '24px', textAlign: 'center' }}>
                    <Alert
                      message={formatMessage({ id: 'document.detail.chunks.empty' })}
                      type="info"
                      showIcon
                    />
                  </div>
                )}
              </Card>
            </Col>
          </Row>
        )}
      </Drawer>
    </>
  );
};
