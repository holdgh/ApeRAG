import { PageContainer, PageHeader } from '@/components';
import { DATETIME_FORMAT, UI_COLLECTION_STATUS } from '@/constants';
import { CollectionConfig } from '@/types';
import { DeleteOutlined } from '@ant-design/icons';
import {
  Badge,
  Button,
  Divider,
  Modal,
  Space,
  Tooltip,
  Typography,
} from 'antd';
import moment from 'moment';
import { useCallback, useMemo } from 'react';
import { toast } from 'react-toastify';
import { FormattedMessage, history, Outlet, useIntl, useModel } from 'umi';

export const LayoutCollection = () => {
  const { collection, deleteCollection } = useModel('collection');
  const [modal, contextHolder] = Modal.useModal();
  const { formatMessage } = useIntl();

  const onDeleteCollection = useCallback(async () => {
    if (!collection?.id) return;
    const confirmed = await modal.confirm({
      title: formatMessage({ id: 'action.confirm' }),
      content: formatMessage(
        { id: 'collection.delete.confirm' },
        { name: collection?.title },
      ),
      okButtonProps: {
        danger: true,
      },
    });
    if (confirmed && (await deleteCollection(collection.id))) {
      toast.success(formatMessage({ id: 'tips.delete.success' }));
      history.push('/collections');
    }
  }, [collection]);

  const config = useMemo(
    () => collection?.config,
    [collection],
  ) as CollectionConfig;

  return (
    <>
      {contextHolder}
      <PageContainer loading={collection === undefined}>
        <PageHeader
          title={collection?.title}
          description={
            <Space split={<Divider type="vertical" />}>
              <Tooltip title={formatMessage({ id: 'text.createdAt' })}>
                <Typography.Text type="secondary">
                  {moment(collection?.created).format(DATETIME_FORMAT)}
                </Typography.Text>
              </Tooltip>
              <Tooltip title={formatMessage({ id: 'collection.source' })}>
                <Typography.Text type="secondary">
                  <FormattedMessage
                    id={`collection.source.${config?.source}`}
                  />
                </Typography.Text>
              </Tooltip>
            </Space>
          }
        >
          <Tooltip title={formatMessage({ id: 'text.status' })}>
            <div>
              <Badge
                status={
                  collection?.status
                    ? UI_COLLECTION_STATUS[collection?.status]
                    : 'default'
                }
                text={
                  <Typography.Text>
                    <FormattedMessage
                      id={`collection.status.${collection?.status}`}
                    />
                  </Typography.Text>
                }
              />
            </div>
          </Tooltip>
          <Tooltip title={formatMessage({ id: 'collection.delete' })}>
            <Button
              icon={<DeleteOutlined />}
              onClick={() => onDeleteCollection()}
              danger
            />
          </Tooltip>
        </PageHeader>
        <Outlet />
      </PageContainer>
    </>
  );
};
