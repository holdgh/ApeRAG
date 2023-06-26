import type { Document } from '@/models/document';
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
  Typography,
  Upload,
  UploadProps,
} from 'antd';
import { ColumnsType } from 'antd/es/table';
import { useEffect, useState } from 'react';

export default () => {
  const [searchKey, setSearchKey] = useState<string | undefined>();
  const [documents, setDocuments] = useState<Document[] | undefined>();
  const [uploadVisible, setUploadVisible] = useState<boolean>(false);
  const { collectionId } = useParams();
  const { modal } = App.useApp();
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
        return record.name?.replace(/.*\./, '').toUpperCase();
      },
    },
    {
      title: 'Size',
      dataIndex: 'size',
    },
    {
      title: 'Status',
      dataIndex: 'status',
    },
    {
      title: 'Last Updated',
      dataIndex: 'updatedAt',
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
    action: 'https://www.mocky.io/v2/5cc8019d300000980a055e76',
    data: {
      a: 1,
      b: 2,
      c: 3,
    },
    onChange(info) {
      const { status } = info.file;
      if (status !== 'uploading') {
        console.log(info.file, info.fileList);
      }
      if (status === 'done') {
      } else if (status === 'error') {
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
          <Button>Merge</Button>
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
