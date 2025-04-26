import { Form, Input } from 'antd';
import { useIntl } from 'umi';

export default () => {
  const { formatMessage } = useIntl();

  return (
    <Form.Item
      name={['config', 'path']}
      rules={[
        {
          required: true,
          message: formatMessage({ id: 'collection.source.local.required' }),
        },
      ]}
      label={formatMessage({ id: 'collection.source.local' })}
    >
      <Input
        placeholder={formatMessage({
          id: 'collection.source.local.placeholder',
        })}
      />
    </Form.Item>
  );
};
