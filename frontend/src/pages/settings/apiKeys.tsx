import { ApiKey } from '@/api';
import { PageContainer, PageHeader, RefreshButton } from '@/components';
import { api } from '@/services';
import { DeleteOutlined, EditOutlined } from '@ant-design/icons';
import { useRequest } from 'ahooks';
import {
  Button,
  Divider,
  Form,
  Input,
  Modal,
  Space,
  Table,
  TableProps,
  Typography,
} from 'antd';
import { useCallback, useMemo, useState } from 'react';
import { toast } from 'react-toastify';
import { FormattedMessage, useIntl } from 'umi';

export default () => {
  const { formatMessage } = useIntl();
  const [modal, contextHolder] = Modal.useModal();
  const [visible, setVisible] = useState<boolean>(false);
  const [form] = Form.useForm<ApiKey>();
  const {
    data: apikeysGetRes,
    run: getApiKeys,
    loading: listLoading,
  } = useRequest(api.apikeysGet);

  const createApiKeys = useCallback(async (values: ApiKey) => {
    await api.apikeysPost({
      apiKeyCreate: values,
    });
    await getApiKeys();
    setVisible(false);
  }, []);
  const updateApiKeys = useCallback(async (values: ApiKey) => {
    if (!values.id) return;
    if (!values.id) return;
    await api.apikeysPut({
      apikeyId: values.id,
      apiKeyUpdate: values,
    });
    getApiKeys();
    setVisible(false);
  }, []);

  const onNewApiKeys = useCallback(async () => {
    form.resetFields();
    setVisible(true);
  }, []);

  const onEditApiKeys = useCallback(async (record: ApiKey) => {
    setVisible(true);
    form.setFieldsValue(record);
  }, []);

  const onDeleteApiKeys = useCallback(async (record: ApiKey) => {
    if (!record.id) return;
    const confirmed = await modal.confirm({
      title: formatMessage({ id: 'action.confirm' }),
      content: formatMessage(
        { id: 'apiKeys.delete.confirm' },
        // { name: collection?.title },
      ),
      okButtonProps: {
        danger: true,
      },
    });
    if (!confirmed) return;

    const res = await api.apikeysApikeyIdDelete({ apikeyId: record.id });
    if (res.status === 200) {
      getApiKeys();
      toast.success(formatMessage({ id: 'tips.delete.success' }));
    }
  }, []);

  const onSave = useCallback(async () => {
    const values = await form.validateFields();
    if (values.id) {
      updateApiKeys(values);
    } else {
      createApiKeys(values);
    }
  }, []);

  const records = useMemo(() => apikeysGetRes?.data.items, [apikeysGetRes]);
  
  const columns: TableProps<ApiKey>['columns'] = useMemo(
    () => [
      {
        title: formatMessage({ id: 'apiKeys.keys' }),
        dataIndex: 'key',
        render: (value) => {
          <Typography.Text copyable={{ text: value }}>{value}</Typography.Text>
        }
      },
      {
        title: formatMessage({ id: 'apiKeys.description' }),
        dataIndex: 'description',
      },
      {
        width: 50,
        render: (value, record) => {
          return (
            <Space>
              <Button
                onClick={() => onEditApiKeys(record)}
                type="text"
                icon={<EditOutlined />}
              />
              <Button
                onClick={() => onDeleteApiKeys(record)}
                type="text"
                danger
                icon={<DeleteOutlined />}
              />
            </Space>
          );
        },
      },
    ],
    [],
  );

  return (
    <>
      {contextHolder}
      <PageContainer>
        <PageHeader
          title={formatMessage({ id: 'apiKeys.title' })}
          description={formatMessage({ id: 'apiKeys.sub_title' })}
        >
          <Button type="primary" onClick={onNewApiKeys}>
            <FormattedMessage id="apiKeys.new" />
          </Button>
          <RefreshButton onClick={() => getApiKeys()} loading={listLoading} />
        </PageHeader>
        <Table
          loading={listLoading}
          rowKey="id"
          columns={columns}
          dataSource={records}
        />
      </PageContainer>

      <Modal
        title={formatMessage({ id: 'apiKeys.title' })}
        open={visible}
        onOk={onSave}
        onCancel={() => setVisible(false)}
      >
        <Divider />

        <Form autoComplete='off' form={form} layout="vertical">
          <Form.Item name="id" hidden>
            <Input />
          </Form.Item>
          <Form.Item
            required
            name="description"
            label={formatMessage({ id: 'apiKeys.description' })}
            rules={[
              {
                required: true,
                message: formatMessage({ id: 'apiKeys.description.required' }),
              },
            ]}
          >
            <Input />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
};
