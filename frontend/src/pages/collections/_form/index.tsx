import { Collection } from '@/api';
import { ApeMarkdown, CheckCard } from '@/components';
import { COLLECTION_SOURCE, COLLECTION_SOURCE_EMAIL } from '@/constants';
import { CollectionConfigSource, CollectionEmailSource } from '@/types';
import {
  Alert,
  Avatar,
  Button,
  Card,
  Divider,
  Form,
  FormInstance,
  Input,
  Radio,
  Segmented,
  Space,
  Switch,
  Typography,
} from 'antd';
import _ from 'lodash';
import { useEffect } from 'react';
import { FormattedMessage, useIntl } from 'umi';
import DocumentCloudFormItems from './DocumentCloudFormItems';
import DocumentEmailFormItems from './DocumentEmailFormItems';
import DocumentFeishuFormItems from './DocumentFeishuFormItems';
import DocumentFtpFormItems from './DocumentFtpFormItems';
import DocumentGithubFormItems from './DocumentGithubFormItems';
import DocumentLocalFormItems from './DocumentLocalFormItems';

type Props = {
  action: 'add' | 'edit';
  values: Collection;
  form: FormInstance<Collection>;
  onSubmit: (data: Collection) => void;
};

export default ({ onSubmit, action, values, form }: Props) => {
  const { formatMessage } = useIntl();

  const source = Form.useWatch(['config', 'source'], form);
  const emailSource: CollectionEmailSource | undefined = Form.useWatch(
    ['config', 'email_source'],
    form,
  );
  const sensitiveProtect = Form.useWatch(['config', 'sensitive_protect'], form);

  const onFinish = async () => {
    const data = await form.validateFields();
    onSubmit(data);
  };

  useEffect(() => {
    if (source === 'ftp') {
      form.setFieldValue(['config', 'port'], 21);
    }
    if (source === 'email') {
      if (!emailSource) {
        form.setFieldValue(['config', 'email_source'], 'gmail');
      } else {
        form.setFieldValue(
          ['config', 'pop_server'],
          COLLECTION_SOURCE_EMAIL[emailSource].pop_server,
        );
        form.setFieldValue(
          ['config', 'port'],
          COLLECTION_SOURCE_EMAIL[emailSource].port,
        );
      }
    }
  }, [source, emailSource]);

  return (
    <Form
      onFinish={onFinish}
      // disabled={readonly}
      layout="vertical"
      form={form}
      initialValues={values}
    >
      <Card style={{ marginBottom: 20 }}>
        <Form.Item
          name="title"
          label={formatMessage({ id: 'text.title' })}
          rules={[
            {
              required: true,
              message: formatMessage({ id: 'text.title.required' }),
            },
          ]}
        >
          <Input />
        </Form.Item>
        <Form.Item
          name="description"
          label={formatMessage({ id: 'text.description' })}
        >
          <Input.TextArea maxLength={300} rows={3} />
        </Form.Item>

        <Form.Item
          label={
            <>
              <Typography.Text>
                {formatMessage({ id: 'text.sensitive.protect' })}
              </Typography.Text>
              &nbsp;
              <Typography.Text type="secondary">
                ({formatMessage({ id: 'text.sensitive.help' })})
              </Typography.Text>
            </>
          }
          valuePropName="checked"
          name={['config', 'sensitive_protect']}
        >
          <Switch />
        </Form.Item>
        {sensitiveProtect ? (
          <>
            <Form.Item
              label={formatMessage({ id: 'text.sensitive.protect.method' })}
              name={['config', 'sensitive_protect_method']}
              required
              rules={[
                {
                  required: true,
                  message: formatMessage({
                    id: 'text.sensitive.protect.method.required',
                  }),
                },
              ]}
            >
              <Radio.Group
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 12,
                }}
                options={[
                  {
                    label: formatMessage({ id: 'text.sensitive.nostore' }),
                    value: 'nostore',
                  },
                  {
                    label: formatMessage({ id: 'text.sensitive.replace' }),
                    value: 'replace',
                  },
                ]}
              />
            </Form.Item>
          </>
        ) : null}

        <Form.Item
          name={['config', 'source']}
          required
          label={formatMessage({ id: 'collection.source' })}
          rules={[
            {
              required: true,
              message: formatMessage({ id: 'collection.source.required' }),
            },
          ]}
        >
          <CheckCard
            options={Object.keys(COLLECTION_SOURCE).map((key) => ({
              label: formatMessage({ id: `collection.source.${key}` }),
              value: key,
              icon: COLLECTION_SOURCE[key as CollectionConfigSource].icon,
              disabled:
                !COLLECTION_SOURCE[key as CollectionConfigSource].enabled ||
                (action === 'edit' && key !== values.config?.source),
            }))}
          />
        </Form.Item>

        {source === 'local' ? <DocumentLocalFormItems /> : null}

        {source === 'email' ? (
          <>
            <Form.Item
              required
              label={formatMessage({ id: 'email.source' })}
              name={['config', 'email_source']}
            >
              <Segmented
                size="small"
                block
                options={_.map(COLLECTION_SOURCE_EMAIL, (conf, key) => ({
                  label: (
                    <Space style={{ padding: 10 }}>
                      <Avatar shape="square" src={conf.icon} size={24} />
                      <Typography.Text>
                        <FormattedMessage id={`email.${key}`} />
                      </Typography.Text>
                    </Space>
                  ),
                  value: key,
                }))}
              />
            </Form.Item>
            <DocumentEmailFormItems />
            {emailSource ? (
              <Form.Item label="">
                <Alert
                  message={formatMessage({
                    id: `email.${emailSource}.tips.title`,
                  })}
                  description={
                    <ApeMarkdown>
                      {formatMessage({
                        id: `email.${emailSource}.tips.description`,
                      })}
                    </ApeMarkdown>
                  }
                  type="info"
                  showIcon
                />
              </Form.Item>
            ) : null}
          </>
        ) : null}

        {source === 's3' || source === 'oss' ? (
          <DocumentCloudFormItems />
        ) : null}

        {source === 'ftp' ? <DocumentFtpFormItems /> : null}

        {source === 'feishu' ? <DocumentFeishuFormItems /> : null}

        {source === 'github' ? <DocumentGithubFormItems /> : null}

        <br />
        <Divider />
        <div style={{ textAlign: 'right' }}>
          <Button style={{ minWidth: 160 }} type="primary" htmlType="submit">
            {formatMessage({ id: 'action.save' })}
          </Button>
        </div>
      </Card>
    </Form>
  );
};
