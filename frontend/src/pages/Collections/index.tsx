import { SnippetsOutlined, VideoCameraOutlined } from '@ant-design/icons';
import { PageContainer } from '@ant-design/pro-components';
import { Link, useModel } from '@umijs/max';
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
  const { collections } = useModel('collection');
  const cardBodyStyle = {
    height: 260,
  };
  const { token } = theme.useToken();
  return (
    <PageContainer ghost>
      <Row gutter={[30, 30]}>
        {collections?.map((collection, key) => {
          return (
            <Col key={key} span={12}>
              <Card bodyStyle={cardBodyStyle} bordered={false}>
                <Typography.Title level={4}>
                  <Space>
                    {collection.type === 'document' ? (
                      <SnippetsOutlined style={{ fontSize: 18 }} />
                    ) : null}
                    {collection.type === 'multimedia' ? (
                      <VideoCameraOutlined style={{ fontSize: 18 }} />
                    ) : null}
                    {collection.title}
                  </Space>
                </Typography.Title>
                <Typography.Text
                  type="secondary"
                  style={{ height: 45, overflow: 'hidden', display: 'block' }}
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
                <Row
                  style={{
                    textAlign: 'center',
                    width: '70%',
                    margin: '0 auto',
                  }}
                >
                  <Col span={12}>
                    <Link to="/">
                      <Button
                        type="primary"
                        style={{ width: 120, display: 'inline-block' }}
                      >
                        Chat
                      </Button>
                    </Link>
                  </Col>
                  <Col span={12}>
                    <Link to={`/collections/${collection.id}/documents`}>
                      <Button style={{ width: 120, display: 'inline-block' }}>
                        View
                      </Button>
                    </Link>
                  </Col>
                </Row>
              </Card>
            </Col>
          );
        })}
      </Row>
    </PageContainer>
  );
};
