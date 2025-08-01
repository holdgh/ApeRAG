import { PageContainer, PageHeader, CollectionMarketplaceCard } from '@/components';
import { SearchOutlined } from '@ant-design/icons';
import {
  Button,
  Col,
  Input,
  Pagination,
  Result,
  Row,
  Space,
  Spin,
  Typography,
} from 'antd';
import { useCallback, useEffect, useState } from 'react';
import { UndrawEmpty } from 'react-undraw-illustrations';
import { FormattedMessage, useIntl, useModel, history } from 'umi';
import { toast } from 'react-toastify';

const { Search } = Input;
const { Text } = Typography;

export default () => {
  const { formatMessage } = useIntl();
  const { 
    marketplaceCollections, 
    marketplaceLoading, 
    marketplacePagination,
    getMarketplaceCollections,
    subscribeToCollection,
    unsubscribeFromCollection,
  } = useModel('collection');
  const { user } = useModel('user');

  const [searchKeyword, setSearchKeyword] = useState<string>('');
  const [subscribing, setSubscribing] = useState<string>(''); // Track which collection is being subscribed

  // Load marketplace collections on page mount
  useEffect(() => {
    getMarketplaceCollections(1, 12);
  }, []);

  const handleSearch = useCallback((value: string) => {
    setSearchKeyword(value);
    // TODO: Implement search functionality when backend supports it
    // For now, just filter by title locally
  }, []);

  const handlePageChange = useCallback((page: number, pageSize?: number) => {
    getMarketplaceCollections(page, pageSize || 12);
  }, [getMarketplaceCollections]);

  const handleCardClick = useCallback((collection: any) => {
    if (!user) return;
    
    if (collection.owner_user_id === user.id) {
      // Owner clicks - go to owner's collection page
      history.push(`/collections/${collection.id}/documents`);
    } else if (collection.subscription_id) {
      // Subscribed collection - go to marketplace collection page
      history.push(`/marketplace/collections/${collection.id}`);
    } else {
      // Not subscribed - show subscribe action
      handleSubscribe(collection.id);
    }
  }, [user]);

  const handleSubscribe = useCallback(async (collectionId: string) => {
    if (!collectionId) return false;
    
    setSubscribing(collectionId);
    try {
      const success = await subscribeToCollection(collectionId);
      if (success) {
        toast.success(formatMessage({ id: 'collection.marketplace.subscribe.success' }));
        return true;
      } else {
        toast.error(formatMessage({ id: 'collection.marketplace.subscribe.failed' }));
        return false;
      }
    } catch (error) {
      toast.error(formatMessage({ id: 'collection.marketplace.subscribe.failed' }));
      return false;
    } finally {
      setSubscribing('');
    }
  }, [subscribeToCollection, formatMessage]);

  const handleUnsubscribe = useCallback(async (collectionId: string) => {
    if (!collectionId) return false;
    
    setSubscribing(collectionId);
    try {
      const success = await unsubscribeFromCollection(collectionId);
      if (success) {
        toast.success(formatMessage({ id: 'collection.marketplace.unsubscribe.success' }));
        return true;
      } else {
        toast.error(formatMessage({ id: 'collection.marketplace.unsubscribe.failed' }));
        return false;
      }
    } catch (error) {
      toast.error(formatMessage({ id: 'collection.marketplace.unsubscribe.failed' }));
      return false;
    } finally {
      setSubscribing('');
    }
  }, [unsubscribeFromCollection, formatMessage]);

  // Filter collections by search keyword
  const filteredCollections = marketplaceCollections?.filter(collection => 
    !searchKeyword || 
    collection.title?.toLowerCase().includes(searchKeyword.toLowerCase()) ||
    collection.description?.toLowerCase().includes(searchKeyword.toLowerCase()) ||
    collection.owner_username?.toLowerCase().includes(searchKeyword.toLowerCase())
  ) || [];

  const renderEmptyState = () => {
    if (marketplaceLoading) {
      return (
        <div style={{ 
          textAlign: 'center', 
          padding: '80px 0',
          background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
          borderRadius: 16,
          margin: '40px 0',
        }}>
          <Spin size="large" />
          <div style={{ marginTop: 16, color: '#8c8c8c', fontSize: '16px' }}>
            正在加载知识库...
          </div>
        </div>
      );
    }

    if (searchKeyword && filteredCollections.length === 0) {
      return (
        <div style={{ 
          background: 'linear-gradient(135deg, #fff5f5 0%, #fed7e2 100%)',
          borderRadius: 16,
          padding: '60px 40px',
          textAlign: 'center',
          margin: '40px 0',
        }}>
          <Result
            icon={<SearchOutlined style={{ fontSize: '48px', color: '#ff7875' }} />}
            title={
              <span style={{ fontSize: '20px', fontWeight: 600, color: '#262626' }}>
                {formatMessage({ id: 'common.search.no.results' })}
              </span>
            }
            subTitle={
              <span style={{ fontSize: '16px', color: '#8c8c8c' }}>
                {formatMessage({ id: 'common.search.try.different.keywords' })}
              </span>
            }
          />
        </div>
      );
    }

    if (!marketplaceCollections || marketplaceCollections.length === 0) {
      return (
        <div style={{ 
          background: 'linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%)',
          borderRadius: 16,
          padding: '80px 40px',
          textAlign: 'center',
          margin: '40px 0',
        }}>
          <Result
            icon={<UndrawEmpty primaryColor="#1890ff" height={240} />}
            title={
              <span style={{ 
                fontSize: '24px', 
                fontWeight: 600, 
                color: '#262626',
                display: 'block',
                marginTop: 16,
              }}>
                <FormattedMessage id="collection.marketplace.empty.title" />
              </span>
            }
            subTitle={
              <span style={{ 
                fontSize: '16px', 
                color: '#8c8c8c',
                lineHeight: '1.5',
                display: 'block',
                marginTop: 8,
              }}>
                <FormattedMessage id="collection.marketplace.empty.description" />
              </span>
            }
          />
        </div>
      );
    }

    return null;
  };

  return (
    <PageContainer loading={marketplaceLoading && !marketplaceCollections}>
      {/* Enhanced Header */}
      <div style={{ 
        textAlign: 'center', 
        marginBottom: 48,
        paddingTop: 24
      }}>
        <div style={{ marginBottom: 24 }}>
          <Typography.Title 
            level={2} 
            style={{ 
              margin: 0, 
              fontWeight: 700,
              fontSize: '32px',
              background: 'linear-gradient(135deg, #1890ff 0%, #722ed1 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
            }}
          >
            <FormattedMessage id="collection.marketplace.title" />
          </Typography.Title>
          <Typography.Text 
            style={{ 
              fontSize: '16px', 
              color: '#8c8c8c',
              marginTop: 8,
              display: 'block',
            }}
          >
            发现并订阅高质量的知识库
          </Typography.Text>
        </div>
        <div style={{ 
          maxWidth: 640, 
          margin: '0 auto',
          padding: '0 20px',
        }}>
          <Search
            placeholder={formatMessage({ id: 'common.search.placeholder' })}
            allowClear
            enterButton={
              <Button 
                type="primary" 
                icon={<SearchOutlined />}
                style={{
                  height: '52px',
                  borderRadius: '0 12px 12px 0',
                  fontSize: '16px',
                  fontWeight: 500,
                  background: 'linear-gradient(135deg, #1890ff 0%, #40a9ff 100%)',
                  border: 'none',
                  boxShadow: '0 4px 12px rgba(24, 144, 255, 0.3)',
                }}
              >
                {formatMessage({ id: 'common.search' })}
              </Button>
            }
            size="large"
            onSearch={handleSearch}
            style={{ 
              width: '100%',
              boxShadow: '0 4px 16px rgba(0, 0, 0, 0.08)',
              borderRadius: 12,
            }}
            styles={{
              input: {
                borderRadius: '12px 0 0 12px',
                fontSize: '16px',
                height: '52px',
                border: '1px solid #e8e8e8',
                borderRight: 'none',
                padding: '0 20px',
              },
            }}
          />
        </div>
      </div>
      
      {marketplaceCollections && marketplaceCollections.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          <Text type="secondary">
            <FormattedMessage 
              id="common.total.items" 
              values={{ total: marketplacePagination.total }} 
            />
          </Text>
        </div>
      )}

      {renderEmptyState() || (
        <>
          <div style={{ 
            background: 'linear-gradient(180deg, rgba(24, 144, 255, 0.02) 0%, rgba(255, 255, 255, 0) 100%)',
            borderRadius: 16,
            padding: '32px 24px',
            marginBottom: 24,
          }}>
            <Row gutter={[24, 24]}>
              {filteredCollections.map((collection) => (
                <Col
                  key={collection.id}
                  xs={24}
                  sm={12}
                  md={12}
                  lg={8}
                  xl={6}
                  xxl={6}
                >
                  <CollectionMarketplaceCard
                    collection={collection}
                    onClick={handleCardClick}
                    onSubscribe={handleSubscribe}
                    onUnsubscribe={handleUnsubscribe}
                    loading={subscribing === collection.id}
                  />
                </Col>
              ))}
            </Row>
          </div>

          {/* Enhanced Pagination */}
          {marketplacePagination.total > marketplacePagination.pageSize && (
            <div style={{ 
              textAlign: 'center', 
              marginTop: 40,
              padding: '24px 0',
              background: '#fafafa',
              borderRadius: 12,
            }}>
              <Pagination
                current={marketplacePagination.current}
                pageSize={marketplacePagination.pageSize}
                total={marketplacePagination.total}
                onChange={handlePageChange}
                showSizeChanger
                showQuickJumper
                showTotal={(total, range) =>
                  formatMessage(
                    { id: 'common.pagination.total' },
                    { start: range[0], end: range[1], total }
                  )
                }
              />
            </div>
          )}
        </>
      )}
    </PageContainer>
  );
};