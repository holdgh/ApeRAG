import { SharedCollection } from '@/api';
import { DATETIME_FORMAT } from '@/constants';
import { ShareAltOutlined, UserOutlined, ClockCircleOutlined, StarOutlined } from '@ant-design/icons';
import { Card, Button, Tag, Typography, Space, Tooltip, Avatar } from 'antd';
import moment from 'moment';
import React from 'react';
import { FormattedMessage, useIntl, useModel } from 'umi';

const { Text, Title } = Typography;

interface CollectionMarketplaceCardProps {
  /**
   * Shared collection data
   */
  collection: SharedCollection;
  /**
   * Callback when clicking the card
   */
  onClick?: (collection: SharedCollection) => void;
  /**
   * Callback when subscribing to collection
   */
  onSubscribe?: (collectionId: string) => Promise<boolean>;
  /**
   * Callback when unsubscribing from collection
   */
  onUnsubscribe?: (collectionId: string) => Promise<boolean>;
  /**
   * Loading state for subscription operations
   */
  loading?: boolean;
}

export const CollectionMarketplaceCard: React.FC<CollectionMarketplaceCardProps> = ({
  collection,
  onClick,
  onSubscribe,
  onUnsubscribe,
  loading = false,
}) => {
  const { formatMessage } = useIntl();
  const { user } = useModel('user');

  const isOwner = user?.id === collection.owner_user_id;
  const isSubscribed = !!collection.subscription_id;
  const canSubscribe = !isOwner && !isSubscribed;
  const canUnsubscribe = !isOwner && isSubscribed;

  // Truncate description to 120 characters for better layout
  const truncatedDescription = React.useMemo(() => {
    if (!collection.description) return '';
    return collection.description.length > 120 
      ? `${collection.description.substring(0, 120)}...`
      : collection.description;
  }, [collection.description]);

  const handleCardClick = () => {
    if (onClick) {
      onClick(collection);
    }
  };

  const handleSubscribe = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onSubscribe) {
      await onSubscribe(collection.id);
    }
  };

  const handleUnsubscribe = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onUnsubscribe) {
      await onUnsubscribe(collection.id);
    }
  };

  const renderActionButton = () => {
    if (isOwner) {
      return (
        <Tag color="gold" icon={<StarOutlined />} style={{ marginLeft: 8, fontSize: '12px' }}>
          <FormattedMessage id="collection.marketplace.owner" />
        </Tag>
      );
    }

    if (canSubscribe) {
      return (
        <Button
          type="primary"
          size="small"
          onClick={handleSubscribe}
          loading={loading}
          icon={<ShareAltOutlined />}
          style={{ 
            borderRadius: 8,
            fontSize: '12px',
            height: '28px',
            marginLeft: 8,
          }}
        >
          <FormattedMessage id="collection.marketplace.subscribe" />
        </Button>
      );
    }

    if (canUnsubscribe) {
      return (
        <Tag color="blue" icon={<ShareAltOutlined />} style={{ marginLeft: 8, fontSize: '12px' }}>
          <FormattedMessage id="collection.marketplace.subscribed" />
        </Tag>
      );
    }

    return null;
  };

  return (
    <Card 
      hoverable={!loading}
      onClick={handleCardClick}
      style={{ 
        height: '100%',
        cursor: loading ? 'default' : 'pointer',
        opacity: loading ? 0.7 : 1,
        borderRadius: 16,
        border: '1px solid #f0f0f0',
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.06)',
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        background: '#ffffff',
        minHeight: '240px',
      }}
      styles={{
        body: {
          padding: '20px',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
        },
      }}
      onMouseEnter={(e) => {
        if (!loading) {
          e.currentTarget.style.boxShadow = '0 8px 24px rgba(0, 0, 0, 0.12)';
          e.currentTarget.style.transform = 'translateY(-4px)';
          e.currentTarget.style.borderColor = '#1890ff';
        }
      }}
      onMouseLeave={(e) => {
        if (!loading) {
          e.currentTarget.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.06)';
          e.currentTarget.style.transform = 'translateY(0)';
          e.currentTarget.style.borderColor = '#f0f0f0';
        }
      }}
    >
      <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
        {/* Header with title */}
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'flex-start',
          marginBottom: 12,
        }}>
          <Title 
            level={5} 
            ellipsis={{ rows: 2, tooltip: collection.title }}
            style={{ 
              margin: 0, 
              flex: 1, 
              marginRight: 8,
              fontWeight: 600,
              fontSize: '16px',
              lineHeight: '1.4',
              color: '#262626',
            }}
          >
            {collection.title}
          </Title>
          {renderActionButton()}
        </div>

        {/* Description */}
        <div style={{ flex: 1, marginBottom: 16 }}>
          <Text 
            style={{ 
              fontSize: '14px',
              lineHeight: '1.5',
              color: '#8c8c8c',
              display: '-webkit-box',
              WebkitLineClamp: 3,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden',
              wordBreak: 'break-word',
            }}
          >
            {truncatedDescription || formatMessage({ id: 'collection.marketplace.no.description' })}
          </Text>
        </div>

        {/* Footer with owner and subscription info */}
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between',
          alignItems: 'center',
          marginTop: 'auto',
          paddingTop: 12,
          borderTop: '1px solid #f5f5f5',
        }}>
          <Space size={8}>
            <Avatar 
              size={20} 
              icon={<UserOutlined />} 
              style={{ backgroundColor: '#1890ff' }}
            />
            <Text style={{ fontSize: '12px', color: '#595959', fontWeight: 500 }}>
              {collection.owner_username}
            </Text>
          </Space>
          
          {collection.gmt_subscribed && isSubscribed && (
            <Tooltip title={formatMessage({ id: 'collection.marketplace.subscribed.at' })}>
              <Space size={4}>
                <ClockCircleOutlined style={{ fontSize: '12px', color: '#bfbfbf' }} />
                <Text style={{ fontSize: '12px', color: '#bfbfbf' }}>
                  {moment(collection.gmt_subscribed).fromNow()}
                </Text>
              </Space>
            </Tooltip>
          )}
        </div>

        {/* Unsubscribe action for subscribed collections */}
        {isSubscribed && !isOwner && (
          <div style={{ marginTop: 12, textAlign: 'center' }}>
            <Button
              type="text"
              size="small"
              onClick={handleUnsubscribe}
              loading={loading}
              danger
              style={{
                fontSize: '12px',
                height: '24px',
                borderRadius: 6,
              }}
            >
              <FormattedMessage id="collection.marketplace.unsubscribe" />
            </Button>
          </div>
        )}
      </div>
    </Card>
  );
};