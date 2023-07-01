import { DOCUMENT_SOURCE_OPTIONS, DocumentConfig } from '@/models/collection';
import { EditOutlined } from '@ant-design/icons';
import {
  Button,
  Card,
  Form,
  Input,
  Modal,
  Radio,
  Space,
  Typography,
  theme,
} from 'antd';
import { useEffect, useState } from 'react';
import styles from './index.less';

type PropsType = {
  value?: string;
  onChange?: (str: string) => void;
  disabled?: boolean;
};

export default ({ value = '', onChange = () => {}, disabled }: PropsType) => {
  const [visible, setVisible] = useState<boolean>(false);
  const [config, setConfig] = useState<DocumentConfig>({
    source: 'system',
  });
  const [form] = Form.useForm();
  const { token } = theme.useToken();

  const onSave = async () => {
    const values = await form.validateFields();
    onChange(JSON.stringify(values));
    setConfig(values);
    setVisible(false);
  };

  useEffect(() => {
    let defaultConfig: DocumentConfig = config;
    try {
      defaultConfig = { ...defaultConfig, ...JSON.parse(value) };
    } catch (err) {}
    form.setFieldsValue(defaultConfig);
    setConfig(defaultConfig);
  }, []);

  const DocumentEdit = (
    <Card
      className={styles.documentEdit}
      onClick={() => {
        if (!disabled) setVisible(true);
      }}
    >
      <Typography.Text type="secondary">
        <EditOutlined /> Document Source
      </Typography.Text>
    </Card>
  );

  // const DocumentInfo = (
  //   <Descriptions
  //     title={<Typography.Text>Document Source</Typography.Text>}
  //     size="small"
  //     bordered
  //     column={{ xs: 1, sm: 2, md: 2 }}
  //     contentStyle={{
  //       color: token.colorTextDisabled,
  //       minWidth: 100,
  //     }}
  //     extra={
  //       <Typography.Link
  //         onClick={() => {
  //           if (!disabled) setVisible(true);
  //         }}
  //       >
  //         <SettingOutlined />
  //       </Typography.Link>
  //     }
  //   >
  //     {_.map(config, (value, key) => {
  //       return (
  //         <Descriptions.Item label={key}>
  //           {value || ''}
  //         </Descriptions.Item>
  //       );
  //     })}
  //   </Descriptions>
  // );

  const localFormItems = (
    <Form.Item
      name="path"
      rules={[
        {
          required: true,
          message: 'local path is required.',
        },
      ]}
      label="Path"
    >
      <Input />
    </Form.Item>
  );

  const cloudFormItems = (
    <>
      <Form.Item
        name="region"
        rules={[
          {
            required: true,
            message: 'region is required.',
          },
        ]}
        label="Region"
      >
        <Input />
      </Form.Item>
      <Form.Item
        name="access_key_id"
        rules={[
          {
            required: true,
            message: 'Access Key is required.',
          },
        ]}
        label="Access Key"
      >
        <Input.Password />
      </Form.Item>
      <Form.Item
        name="secret_access_key"
        rules={[
          {
            required: true,
            message: 'Secret Access Key is required.',
          },
        ]}
        label="Secret Access Key"
      >
        <Input.Password />
      </Form.Item>
      <Form.Item
        name="bucket"
        rules={[
          {
            required: true,
            message: 'bucket is required.',
          },
        ]}
        label="Bucket"
      >
        <Input />
      </Form.Item>
      <Form.Item name="dir" label="Directory">
        <Input />
      </Form.Item>
    </>
  );

  const ftpFormItems = (
    <>
      <Form.Item
        name="host"
        rules={[
          {
            required: true,
            message: 'host is required.',
          },
        ]}
        label="Host"
      >
        <Input />
      </Form.Item>
      <Form.Item
        name="username"
        rules={[
          {
            required: true,
            message: 'username is required.',
          },
        ]}
        label="Username"
      >
        <Input />
      </Form.Item>
      <Form.Item
        name="password"
        rules={[
          {
            required: true,
            message: 'password is required.',
          },
        ]}
        label="Password"
      >
        <Input.Password />
      </Form.Item>
    </>
  );

  return (
    <>
      {DocumentEdit}
      <Modal
        title="Document Config"
        open={visible}
        onCancel={() => setVisible(false)}
        footer={
          <Space>
            <Button onClick={() => setVisible(false)}>Cancel</Button>
            <Button type="primary" onClick={onSave}>
              Save
            </Button>
          </Space>
        }
      >
        <br />
        <Form
          form={form}
          layout="vertical"
          onValuesChange={(changedValues, allValues) => setConfig(allValues)}
        >
          <Form.Item
            name="source"
            rules={[
              {
                required: true,
                message: 'source is required.',
              },
            ]}
            label="Source"
          >
            <Radio.Group options={DOCUMENT_SOURCE_OPTIONS} />
          </Form.Item>
          {config.source === 'local' ? localFormItems : null}
          {config.source === 's3' || config.source === 'oss'
            ? cloudFormItems
            : null}
          {config.source === 'ftp' ? ftpFormItems : null}
        </Form>
      </Modal>
    </>
  );
};
