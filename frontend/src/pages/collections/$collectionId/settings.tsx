import { Collection } from '@/api';
import { ShareAltOutlined } from '@ant-design/icons';
import { Form, Card, Switch, Typography, Divider, message } from 'antd';
import { useEffect, useState } from 'react';
import { toast } from 'react-toastify';
import { useIntl, useModel, useParams } from 'umi';
import CollectionForm from '../_form';

const { Title, Text } = Typography;

export default () => {
  const { formatMessage } = useIntl();
  const [form] = Form.useForm<Collection>();
  const { collection, updateCollection } = useModel('collection');
  const { collectionId } = useParams();
  
  // 分享状态
  const [isPublished, setIsPublished] = useState(false);
  const [publishing, setPublishing] = useState(false);
  
  const { 
    sharingStatus,
    sharingLoading,
    getSharingStatus,
    publishCollection,
    unpublishCollection,
  } = useModel('collection');

  // 加载分享状态
  useEffect(() => {
    if (collectionId && getSharingStatus) {
      getSharingStatus(collectionId);
    }
  }, [collectionId]);

  // 更新本地状态
  useEffect(() => {
    if (sharingStatus) {
      setIsPublished(sharingStatus.is_published || false);
    }
  }, [sharingStatus]);

  const onFinish = async (values: Collection) => {
    const updated = await updateCollection(values);
    if (updated) {
      toast.success(formatMessage({ id: 'tips.update.success' }));
    }
  };

  const handlePublishToggle = async (checked: boolean) => {
    if (!collectionId) return;
    
    setPublishing(true);
    try {
      if (checked) {
        await publishCollection(collectionId);
        message.success('知识库已发布到市场');
      } else {
        await unpublishCollection(collectionId);
        message.success('知识库已从市场下架');
      }
      setIsPublished(checked);
    } catch (error) {
      message.error(checked ? '发布失败' : '下架失败');
    } finally {
      setPublishing(false);
    }
  };

  return (
    <Card>
      <CollectionForm
        form={form}
        onSubmit={onFinish}
        action="edit"
        values={collection}
      />
      
      <Divider style={{ margin: '40px 0 24px' }} />
      
      <div style={{ marginBottom: 24 }}>
        <Title level={4} style={{ marginBottom: 16 }}>
          分享
        </Title>
        
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          padding: '16px 0'
        }}>
          <div>
            <Text strong>发布到知识库市场</Text>
            <br />
            <Text type="secondary" style={{ fontSize: '14px' }}>
              发布后其他用户可以订阅使用（只读模式）
            </Text>
          </div>
          
          <Switch
            checked={isPublished}
            loading={sharingLoading || publishing}
            onChange={handlePublishToggle}
          />
        </div>
      </div>
    </Card>
  );
};