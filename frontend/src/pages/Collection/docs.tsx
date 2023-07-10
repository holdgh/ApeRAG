import { DOCUMENT_STATUS_TAG_COLORS } from '@/constants';
import { getUser } from '@/models/user';
import {
  DeleteCollectionDocument,
  GetCollectionDocuments,
} from '@/services/documents';
import type { TypesDocument, TypesDocumentConfig } from '@/types';
import { DeleteOutlined, UploadOutlined } from '@ant-design/icons';
import { useModel, useParams } from '@umijs/max';
import {
  App,
  Button,
  Card,
  Input,
  Space,
  Table,
  Tag,
  Tooltip,
  Typography,
  Upload,
  UploadProps,
} from 'antd';
import { ColumnsType } from 'antd/es/table';
import byteSize from 'byte-size';
import _ from 'lodash';
import moment from 'moment';
import { useEffect, useState } from 'react';

export default () => {
  const [loading, setLoading] = useState<boolean>(false);
  const [searchKey, setSearchKey] = useState<string | undefined>();
  const [documents, setDocuments] = useState<TypesDocument[] | undefined>();
  const { collectionId } = useParams();
  const { modal, message } = App.useApp();
  const user = getUser();
  const { getCollection } = useModel('collection');
  const collection = getCollection(collectionId);
  const config = collection?.config as TypesDocumentConfig;

  const dataSource = documents?.filter((d) =>
    new RegExp(searchKey || '').test(d.name),
  );

  const getDocuments = async () => {
    setLoading(true);
    const { data } = await GetCollectionDocuments(String(collectionId));
    setDocuments(data);
    setLoading(false);
  };

  const onDelete = (record: TypesDocument) => {
    if (!collectionId) return;
    modal.confirm({
      title: 'Comfirm',
      content: `delete ${record.name}?`,
      onOk: async () => {
        await DeleteCollectionDocument(collectionId, record.id);
        getDocuments();
      },
    });
  };

  const columns: ColumnsType<TypesDocument> = [
    {
      title: 'Name',
      dataIndex: 'name',
      render: (_value, record) => {
        return (
          <Tooltip placement="left" title={record.name}>
            <Typography.Text style={{ maxWidth: 300 }} ellipsis={true}>
              {record.name}
            </Typography.Text>
          </Tooltip>
        );
      },
    },
    {
      title: 'Type',
      dataIndex: 'type',
      width: 80,
      render: (_value, record) => {
        return (
          <Typography.Text type="secondary" ellipsis={true}>
            {record.name
              .substring(record.name.lastIndexOf('.') + 1)
              .toUpperCase()}
          </Typography.Text>
        );
      },
    },
    {
      title: 'Size',
      dataIndex: 'size',
      width: 100,
      render: (_value, record) => {
        return (
          <Typography.Text type="secondary" ellipsis={true}>
            {byteSize(record.size || 0).toString()}
          </Typography.Text>
        );
      },
    },
    {
      title: 'Status',
      dataIndex: 'status',
      width: 120,
      render: (_value, record) => {
        return (
          <Tag color={DOCUMENT_STATUS_TAG_COLORS[record.status]}>
            {_.capitalize(record.status)}
          </Tag>
        );
      },
    },
    {
      title: 'Created At',
      width: 140,
      render: (_value, record) => {
        return (
          <Typography.Text type="secondary" ellipsis={true}>
            {moment(record.created).fromNow()}
          </Typography.Text>
        );
      },
    },
    {
      title: 'Actions',
      width: 80,
      align: 'center',
      render: (_value, record) => {
        return (
          <Button
            onClick={() => onDelete(record)}
            type="ghost"
            size="small"
            shape="circle"
          >
            <DeleteOutlined />
          </Button>
        );
      },
    },
  ];

  const uploadProps: UploadProps = {
    name: 'file',
    multiple: true,
    action: `${API_ENDPOINT}/api/v1/collections/${collectionId}/documents`,
    data: {},
    showUploadList: false,
    headers: {
      Authorization: 'Bearer ' + user?.__raw,
    },
    onChange(info) {
      const { status } = info.file;
      if (status === 'done') {
        getDocuments();
      } else if (status === 'error') {
        message.error('upload error');
      }
    },
  };

  useEffect(() => {
    getDocuments();
    const timer = setInterval(getDocuments, 5000);
    return () => {
      clearInterval(timer);
    };
  }, []);

  return (
    <Card bordered={false}>
      <Space style={{ width: '100%', justifyContent: 'space-between' }}>
        <Input.Search
          allowClear
          style={{ width: 300 }}
          value={searchKey}
          onChange={(e) => {
            setSearchKey(e.currentTarget.value);
          }}
        />

        {collection?.type === 'document' && config?.source === 'system' ? (
          <Space>
            <Button disabled>Merge</Button>
            <Upload {...uploadProps}>
              <Button type="primary" icon={<UploadOutlined />}>
                Add Documents
              </Button>
            </Upload>
          </Space>
        ) : null}
      </Space>
      <br />
      <br />
      <Table
        loading={loading}
        rowKey="id"
        columns={columns}
        dataSource={dataSource}
      />
    </Card>
  );
};
