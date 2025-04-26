import { Register } from '@/api';
import bgDark from '@/assets/page/signin-dark.svg';
import bgLight from '@/assets/page/signin-light.svg';
import { PageContainer } from '@/components';
import { api } from '@/services';
import { KeyOutlined, MailOutlined, UserOutlined } from '@ant-design/icons';
import { Button, Card, Divider, Form, Input, Space, Typography } from 'antd';
import { useCallback } from 'react';
import { toast } from 'react-toastify';
import {
  FormattedMessage,
  history,
  Link,
  useIntl,
  useModel,
  useSearchParams,
} from 'umi';

export default () => {
  const [form] = Form.useForm<Register & { password_repeat?: string }>();
  const { formatMessage } = useIntl();
  const { themeName, loading, setLoading } = useModel('global');

  const [searchParams] = useSearchParams();
  const redirectUri = searchParams.get('redirectUri');
  const redirectString = redirectUri
    ? '?redirectUri=' + encodeURIComponent(redirectUri)
    : '';

  const onFinish = useCallback(async () => {
    const values = await form.validateFields();

    if (values.password !== values.password_repeat) {
      toast.error(formatMessage({ id: 'user.password_repeat_error' }));
      return;
    }

    setLoading(true);
    const res = await api.registerPost({ register: values });
    setLoading(false);
    if (res.status === 200) {
      toast.success(formatMessage({ id: 'user.signup_success' }));
      history.push(`/accounts/signin${redirectString}`);
    }
  }, []);

  return (
    <PageContainer
      height="fixed"
      width="auto"
      style={{
        backgroundImage: `url(${themeName === 'dark' ? bgDark : bgLight})`,
        backgroundPosition: 'top center',
        backgroundRepeat: 'no-repeat',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexFlow: 'wrap',
      }}
    >
      <Card variant="borderless" style={{ width: 400 }}>
        <Space style={{ display: 'flex', justifyContent: 'space-between' }}>
          <Typography.Title level={3} style={{ margin: 0 }}>
            <FormattedMessage id="user.signup" />
          </Typography.Title>
        </Space>
        <Divider />
        <Form
          form={form}
          layout="vertical"
          size="large"
          onFinish={onFinish}
          autoComplete="off"
        >
          <Form.Item
            name="username"
            required
            label={formatMessage({ id: 'user.username' })}
            rules={[
              {
                required: true,
                message: formatMessage({ id: 'user.username_required' }),
              },
            ]}
          >
            <Input
              prefix={
                <Typography.Text type="secondary">
                  <UserOutlined />
                </Typography.Text>
              }
              style={{ fontSize: 'inherit' }}
              placeholder={formatMessage({ id: 'user.username' })}
            />
          </Form.Item>
          <Form.Item name="email" label={formatMessage({ id: 'user.email' })}>
            <Input
              type="email"
              prefix={
                <Typography.Text type="secondary">
                  <MailOutlined />
                </Typography.Text>
              }
              style={{ fontSize: 'inherit' }}
              placeholder={formatMessage({ id: 'user.email' })}
            />
          </Form.Item>
          <Form.Item
            required
            name="password"
            label={formatMessage({ id: 'user.password' })}
            rules={[
              {
                required: true,
                message: formatMessage({ id: 'user.password_required' }),
              },
            ]}
          >
            <Input.Password
              prefix={
                <Typography.Text type="secondary">
                  <KeyOutlined />
                </Typography.Text>
              }
              style={{ fontSize: 'inherit' }}
              placeholder={formatMessage({ id: 'user.password' })}
            />
          </Form.Item>
          <Form.Item
            name="password_repeat"
            label={formatMessage({ id: 'user.password_repeat' })}
            rules={[
              {
                required: true,
                message: formatMessage({ id: 'user.password_repeat_required' }),
              },
            ]}
          >
            <Input.Password
              prefix={
                <Typography.Text type="secondary">
                  <KeyOutlined />
                </Typography.Text>
              }
              style={{ fontSize: 'inherit' }}
              placeholder={formatMessage({ id: 'user.password_repeat' })}
            />
          </Form.Item>

          <Button loading={loading} htmlType="submit" block type="primary">
            <FormattedMessage id="user.signup" />
          </Button>
        </Form>

        <Divider />
        <Space
          style={{
            display: 'flex',
            justifyContent: 'center',
            marginTop: 4,
          }}
        >
          <Typography.Text type="secondary">
            <FormattedMessage id="user.have_account" />
          </Typography.Text>
          <Link to={`/accounts/signin${redirectString}`}>
            <FormattedMessage id="user.signin" />
          </Link>
        </Space>
      </Card>
    </PageContainer>
  );
};
