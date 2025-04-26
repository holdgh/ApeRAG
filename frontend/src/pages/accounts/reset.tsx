import { ChangePassword } from '@/api';
import bgDark from '@/assets/page/signin-dark.svg';
import bgLight from '@/assets/page/signin-light.svg';
import { PageContainer } from '@/components';
import { api } from '@/services';
import { KeyOutlined, UserOutlined } from '@ant-design/icons';
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
  const [form] = Form.useForm<ChangePassword>();
  const { formatMessage } = useIntl();
  const [searchParams] = useSearchParams();
  const { themeName } = useModel('global');
  const redirectUri = searchParams.get('redirectUri');
  const redirectString = redirectUri
    ? '?redirectUri=' + encodeURIComponent(redirectUri)
    : '';

  const onFinish = useCallback(async () => {
    const values = await form.validateFields();

    const res = await api.changePasswordPost({
      changePassword: values,
    });
    if (res.status === 200) {
      toast.success(formatMessage({ id: 'user.password_reset_success' }));
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
            <FormattedMessage id="user.password_reset" />
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
            required
            name="username"
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
          <Form.Item
            name="old_password"
            required
            label={formatMessage({ id: 'user.password_old' })}
            rules={[
              {
                required: true,
                message: formatMessage({ id: 'user.password_old_required' }),
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
              placeholder={formatMessage({ id: 'user.password_old' })}
            />
          </Form.Item>
          <Form.Item
            name="new_password"
            required
            label={formatMessage({ id: 'user.password_new' })}
            rules={[
              {
                required: true,
                message: formatMessage({ id: 'user.password_new_required' }),
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
              placeholder={formatMessage({ id: 'user.password_new' })}
            />
          </Form.Item>

          <Button htmlType="submit" block type="primary">
            <FormattedMessage id="user.password_reset" />
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
