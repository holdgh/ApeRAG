import CollectionTitle from '@/components/CollectionTitle';
import { PageContainer } from '@ant-design/pro-components';
import { Link, history, useModel } from '@umijs/max';
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
import _ from 'lodash';

export default () => {
  const {
    collections,
    setCurrentCollection,
    getCollectionUrl,
    parseCollectionConfig,
  } = useModel('collection');
  const { token } = theme.useToken();

  const btnSize = 'middle';
  const btnWidth = 120;
  const cardHeight = 220;

  return (
    <PageContainer ghost>
      <Row gutter={[30, 30]}>
        {collections?.map((collection, key) => {
          const config = parseCollectionConfig(collection);
          return (
            <Col key={key} xs={24} sm={24} md={24} lg={12} xl={12} xxl={12}>
              <Card
                bordered={false}
                bodyStyle={{
                  height: cardHeight,
                  display: 'flex',
                  flexDirection: 'column',
                }}
              >
                <CollectionTitle collection={collection} />
                <Typography.Text
                  type="secondary"
                  ellipsis
                  style={{
                    display: 'block',
                  }}
                >
                  {collection.description}
                </Typography.Text>
                <div
                  style={{
                    margin: '20px 0',
                    flex: 1,
                    verticalAlign: 'middle',
                  }}
                >
                  <Space
                    style={{
                      justifyContent: 'space-around',
                      width: '100%',
                    }}
                    split={<Divider type="vertical" style={{ height: 30 }} />}
                  >
                    <Statistic
                      title="Status"
                      value={_.capitalize(collection.status)}
                      valueStyle={{
                        fontSize: 16,
                        color:
                          collection.status === 'ACTIVE'
                            ? token.colorText
                            : token.colorError,
                      }}
                    />
                    <Statistic
                      title={
                        collection.type === 'database' ? 'Database' : 'Source'
                      }
                      value={_.capitalize(
                        config.source || config.db_type || 'System',
                      )}
                      valueStyle={{ fontSize: 16 }}
                    />
                    {collection?.type === 'document' ? (
                      <Statistic
                        title="Documents"
                        value="--"
                        valueStyle={{ fontSize: 16 }}
                      />
                    ) : null}
                  </Space>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <Space size="large">
                    <Button
                      size={btnSize}
                      type="primary"
                      style={{ width: btnWidth, display: 'inline-block' }}
                      onClick={async () => {
                        await setCurrentCollection(collection);
                        history.push('/chat');
                      }}
                    >
                      Chat
                    </Button>
                    <Link to={getCollectionUrl(collection)}>
                      <Button
                        size={btnSize}
                        style={{
                          width: btnWidth,
                          display: 'inline-block',
                        }}
                      >
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
