import { DOCUMENT_SOURCE_OPTIONS } from '@/constants';
import type { TypesDocumentConfig } from '@/types';
import { EditOutlined, SettingOutlined } from '@ant-design/icons';
import {
  Button,
  Card,
  Descriptions,
  Form,
  Modal,
  Radio,
  Space,
  Typography,
  theme,
} from 'antd';
import { useEffect, useState } from 'react';

import {
  getCloudDescItems,
  getCloudFormItems,
  getEmailDescItems,
  getEmailFormItems,
  getFtpDescItems,
  getFtpFormItems,
  getLocalDescItems,
  getLocalFormItems,
} from './utils';

import styles from './index.less';

type PropsType = {
  value?: string;
  onChange?: (str: string) => void;
  disabled?: boolean;
};

export default ({ value = '', onChange = () => {}, disabled }: PropsType) => {
  const [visible, setVisible] = useState<boolean>(false);
  const [originConfig, setOriginConfig] = useState<TypesDocumentConfig>({
    source: 'system',
  });
  const [config, setConfig] = useState<TypesDocumentConfig>({
    source: 'system',
  });

  const [form] = Form.useForm();
  const { token } = theme.useToken();

  const onSave = async () => {
    const values = await form.validateFields();
    onChange(JSON.stringify(values));

    setOriginConfig(values);
    setVisible(false);
  };

  useEffect(() => {
    let defaultConfig: TypesDocumentConfig = config;
    try {
      defaultConfig = { ...defaultConfig, ...JSON.parse(value) };
    } catch (err) {}
    form.setFieldsValue(defaultConfig);
    setConfig(defaultConfig);
    setOriginConfig(defaultConfig);
  }, []);

  const DocumentEdit = disabled ? null : (
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

  const DocumentInfo = (
    <Descriptions
      title={<Typography.Text>Document Source</Typography.Text>}
      size="small"
      bordered
      column={{ xs: 1, sm: 2, md: 2 }}
      contentStyle={{
        color: token.colorTextDisabled,
        minWidth: 100,
      }}
      extra={
        disabled ? null : (
          <Button
            shape="circle"
            type="text"
            disabled={disabled}
            onClick={() => {
              setVisible(true);
            }}
          >
            <SettingOutlined />
          </Button>
        )
      }
    >
      <Descriptions.Item label="Source">
        {originConfig.source || ''}
      </Descriptions.Item>

      {originConfig.source === 'local' ? getLocalDescItems(originConfig) : null}
      {originConfig.source === 'email' ? getEmailDescItems(originConfig) : null}
      {originConfig.source === 's3' || originConfig.source === 'oss'
        ? getCloudDescItems(originConfig)
        : null}
      {originConfig.source === 'ftp' ? getFtpDescItems(originConfig) : null}
    </Descriptions>
  );

  return (
    <>
      {originConfig.source === 'system' ? DocumentEdit : DocumentInfo}
      <Modal
        title="Document Source"
        open={visible}
        onCancel={() => setVisible(false)}
        destroyOnClose={true}
        width={560}
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
          onValuesChange={async (changedValues, allValues) => {
            setConfig(allValues);
          }}
        >
          <Form.Item
            name="source"
            rules={[
              {
                required: true,
                message: 'source is required.',
              },
            ]}
            label="Document Source"
          >
            <Radio.Group options={DOCUMENT_SOURCE_OPTIONS} />
          </Form.Item>
          {config.source === 'local' ? getLocalFormItems() : null}
          {config.source === 'email' ? getEmailFormItems() : null}
          {config.source === 's3' || config.source === 'oss'
            ? getCloudFormItems()
            : null}
          {config.source === 'ftp' ? getFtpFormItems() : null}
        </Form>
      </Modal>
    </>
  );
};
