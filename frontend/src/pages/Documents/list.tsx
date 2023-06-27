import type { Document } from '@/models/document';
import { getUser } from '@/models/user';
import {
  DeleteCollectionDocument,
  GetCollectionDocuments,
} from '@/services/documents';
import {
  DeleteOutlined,
  InboxOutlined,
  UploadOutlined,
} from '@ant-design/icons';
import { useParams } from '@umijs/max';
import {
  App,
  Button,
  Card,
  Input,
  Modal,
  Space,
  Table,
  Tag,
  Typography,
  Upload,
  UploadProps,
} from 'antd';
import { ColumnsType } from 'antd/es/table';
import moment from 'moment';
import { useEffect, useState } from 'react';

export default () => {
  const [searchKey, setSearchKey] = useState<string | undefined>();
  const [documents, setDocuments] = useState<Document[] | undefined>();
  const [uploadVisible, setUploadVisible] = useState<boolean>(false);
  const { collectionId } = useParams();
  const { modal, message } = App.useApp();
  const user = getUser();

  const dataSource = documents?.filter((d) =>
    new RegExp(searchKey || '').test(d.name),
  );

  const getDocuments = async () => {
    const { data } = await GetCollectionDocuments(String(collectionId));
    setDocuments(data);
  };

  const onDelete = (record: Document) => {
    if (!collectionId) return;
    modal.confirm({
      title: 'Comfirm',
      content: `delete ${record.name}?`,
      onOk: () => {
        DeleteCollectionDocument(collectionId, record.id);
        getDocuments();
      },
    });
  };

  const columns: ColumnsType<Document> = [
    {
      title: 'Name',
      dataIndex: 'name',
    },
    {
      title: 'Type',
      dataIndex: 'type',
      render: (_value, record) => {
        return (
          <Typography.Text type="secondary">
            {record.name?.replace(/.*\./, '').toUpperCase()}
          </Typography.Text>
        );
      },
    },
    {
      title: 'Size',
      dataIndex: 'size',
      render: (_value, record) => {
        return (
          <Typography.Text type="secondary">{record.size}</Typography.Text>
        );
      },
    },
    {
      title: 'Status',
      dataIndex: 'status',
      render: (_value, record) => {
        return (
          <Tag color={record.status === 'FAILED' ? 'error' : 'default'}>
            {record.status}
          </Tag>
        );
      },
    },
    {
      title: 'Created At',
      render: (_value, record) => {
        return (
          <Typography.Text type="secondary">
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
    action: `/api/v1/collections/${collectionId}/documents`,
    data: {},
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
        <Space>
          <Button disabled>Merge</Button>
          <Button
            type="primary"
            onClick={() => {
              setUploadVisible(true);
            }}
            icon={<UploadOutlined />}
          >
            Add Documents
          </Button>
        </Space>
      </Space>
      <br />
      <br />
      <Table rowKey="id" columns={columns} dataSource={dataSource} />
      <Modal
        title="Upload Documents"
        open={uploadVisible}
        onCancel={() => {
          setUploadVisible(false);
        }}
        footer={false}
      >
        <Upload.Dragger {...uploadProps}>
          <p className="ant-upload-drag-icon">
            <InboxOutlined />
          </p>
          <Typography.Paragraph type="secondary">
            Click or drag file to this area to upload
          </Typography.Paragraph>
          <Typography.Paragraph type="secondary">
            Support for a single or bulk upload. Strictly prohibited from
            uploading company data or other banned files.
          </Typography.Paragraph>
        </Upload.Dragger>
      </Modal>
    </Card>
  );
};
