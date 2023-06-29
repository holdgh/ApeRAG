import CollectionTitle from '@/components/CollectionTitle';
import { PageContainer } from '@ant-design/pro-components';
import { Link, history, useModel } from '@umijs/max';
import { getCollectionUrl } from '@/models/collection';
import {
  Button,
  Card,
  Col,
  Divider,
  Row,
  Space,
  Statistic,
  Typography,
  theme,
} from 'antd';

export default () => {
  const { collections, setCurrentCollection } = useModel('collection');
  const cardBodyStyle = {
    height: 260,
  };
  const { token } = theme.useToken();
  return (
    <PageContainer ghost>
      <Row gutter={[30, 30]}>
        {collections?.map((collection, key) => {
          return (
            <Col
              key={key}
              span={12}
              xs={24}
              sm={24}
              md={24}
              lg={12}
              xl={12}
              xxl={12}
            >
              <Card bodyStyle={cardBodyStyle} bordered={false}>
                <CollectionTitle collection={collection} />
                <Typography.Text
                  type="secondary"
                  style={{
                    maxHeight: 45,
                    minHeight: 25,
                    overflow: 'hidden',
                    display: 'block',
                  }}
                >
                  {collection.description}
                </Typography.Text>
                <Card bordered={false}>
                  <Space
                    style={{ justifyContent: 'space-around', width: '100%' }}
                  >
                    <Statistic
                      title="Status"
                      value={collection.status}
                      valueStyle={{
                        fontSize: 16,
                        color:
                          collection.status === 'ACTIVE'
                            ? token.colorText
                            : token.colorWarning,
                      }}
                    />
                    <Divider type="vertical" style={{ height: 30 }} />
                    <Statistic
                      title="Type"
                      value={collection.type}
                      valueStyle={{ fontSize: 16 }}
                    />
                    <Divider type="vertical" style={{ height: 30 }} />
                    <Statistic
                      title="Documents"
                      value={12}
                      valueStyle={{ fontSize: 16 }}
                    />
                  </Space>
                </Card>
                <div style={{ textAlign: 'center' }}>
                  <Space size="large">
                    <Button
                      type="primary"
                      style={{ width: 120, display: 'inline-block' }}
                      onClick={async () => {
                        await setCurrentCollection(collection);
                        history.push('/chat');
                      }}
                    >
                      Chat
                    </Button>
                    <Link to={getCollectionUrl(collection)}>
                      <Button style={{ width: 120, display: 'inline-block' }}>
                        View
                      </Button>
                    </Link>
                  </Space>
                </div>
              </Card>
            </Col>
          );
        })}
      </Row>
    </PageContainer>
  );
};
