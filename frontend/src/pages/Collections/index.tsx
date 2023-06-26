import {
  PlusOutlined,
  SnippetsOutlined,
  VideoCameraOutlined,
} from '@ant-design/icons';
import { PageContainer } from '@ant-design/pro-components';
import { Link, useModel } from '@umijs/max';
import {
  Button,
  Card,
  Col,
  Row,
  Space,
  Statistic,
  Typography,
  theme,
} from 'antd';

export default () => {
  const { collections } = useModel('collection');
  const cardBodyStyle = {
    height: 290,
  };
  const { token } = theme.useToken();
  return (
    <PageContainer
      ghost
      extra={[
        <Link key={1} to="/collections/new">
          <Button type="primary" icon={<PlusOutlined />}>
            Create a Collection
          </Button>
        </Link>,
      ]}
    >
      <Row gutter={[30, 30]}>
        {collections.map((collection, key) => {
          return (
            <Col key={key} span={12}>
              <Card bodyStyle={cardBodyStyle} bordered={false}>
                <Typography.Title level={4}>
                  <Space>
                    {collection.type === 'Document' ? (
                      <SnippetsOutlined style={{ fontSize: 24 }} />
                    ) : null}
                    {collection.type === 'Multimedia' ? (
                      <VideoCameraOutlined style={{ fontSize: 24 }} />
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
                <br />
                <br />
                <Space
                  style={{ justifyContent: 'space-around', width: '100%' }}
                >
                  <Statistic
                    title="Status"
                    value={collection.status}
                    valueStyle={{
                      fontSize: 16,
                      color:
                        collection.status === 'Active'
                          ? token.colorSuccess
                          : token.colorWarning,
                    }}
                  />
                  <Statistic
                    title="Type"
                    value={collection.type}
                    valueStyle={{ fontSize: 16 }}
                  />
                  <Statistic
                    title="Documents"
                    value={12}
                    valueStyle={{ fontSize: 16 }}
                  />
                </Space>
                <br />
                <br />
                <Row style={{ textAlign: 'center' }}>
                  <Col span={12}>
                    <Link to="/">
                      <Button
                        type="primary"
                        style={{ width: 150, display: 'inline-block' }}
                      >
                        Chat
                      </Button>
                    </Link>
                  </Col>
                  <Col span={12}>
                    <Link to={`/collections/${collection.id}/documents`}>
                      <Button style={{ width: 150, display: 'inline-block' }}>
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
