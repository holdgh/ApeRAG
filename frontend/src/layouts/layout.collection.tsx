import { PageContainer, PageHeader } from '@/components';
import { DATETIME_FORMAT, UI_COLLECTION_STATUS } from '@/constants';
import { CollectionConfig } from '@/types';
import { DeleteOutlined } from '@ant-design/icons';
import {
  Badge,
  Button,
  Divider,
  Menu,
  MenuProps,
  Modal,
  Space,
  Tooltip,
  Typography,
} from 'antd';
import moment from 'moment';
import { useCallback, useEffect, useMemo } from 'react';
import { toast } from 'react-toastify';
import {
  FormattedMessage,
  history,
  Outlet,
  useIntl,
  useLocation,
  useModel,
  useParams,
} from 'umi';
import { BodyContainer } from './body';
import { Navbar, NavbarBody, NavbarHeader } from './navbar';
import Sidebar from './sidebar';

type MenuItem = Required<MenuProps>['items'][number];

const Navigation = () => {
  const { collectionId } = useParams();
  const { collection } = useModel('collection');
  const location = useLocation();

  const menuItems = useMemo(
    (): MenuItem[] => [
      {
        label: <FormattedMessage id="collection.files" />,
        key: `/collections/${collectionId}/documents`,
      },
      {
        label: <FormattedMessage id="collection.sync" />,
        key: `/collections/${collectionId}/sync`,
        disabled: true,
      },
      {
        label: <FormattedMessage id="collection.questions" />,
        key: `/collections/${collectionId}/questions`,
        disabled: true,
      },
      {
        label: <FormattedMessage id="collection.settings" />,
        key: `/collections/${collectionId}/settings`,
      },
    ],
    [collectionId],
  );

  if (!collection) return;

  return (
    <Navbar>
      <NavbarHeader title={collection?.title} backTo="/collections" />
      <NavbarBody>
        <Menu
          onClick={({ key }) => history.push(key)}
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          style={{
            padding: 0,
            background: 'none',
            border: 'none',
          }}
        />
      </NavbarBody>
    </Navbar>
  );
};

export default () => {
  const { collectionId } = useParams();
  const { collection, getCollection, setCollection, deleteCollection } =
    useModel('collection');
  const [modal, contextHolder] = Modal.useModal();
  const { formatMessage } = useIntl();

  const isDetail = collectionId !== undefined;

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

  useEffect(() => {
    if (collectionId) {
      getCollection(collectionId);
    } else {
      setCollection(undefined);
    }
    return () => setCollection(undefined);
  }, [collectionId]);

  const config = useMemo(
    () => collection?.config,
    [collection],
  ) as CollectionConfig;

  return (
    <>
      {contextHolder}
      <Sidebar />
      {isDetail && (
        <>
          <Navigation />
          <BodyContainer sidebar={true} navbar={true}>
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
          </BodyContainer>
        </>
      )}

      {!isDetail && (
        <BodyContainer sidebar={true} navbar={false}>
          <Outlet />
        </BodyContainer>
      )}
    </>
  );
};
