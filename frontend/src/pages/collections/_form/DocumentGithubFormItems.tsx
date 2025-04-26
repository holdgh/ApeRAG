import { Form, Input } from 'antd';
import { useIntl } from 'umi';

export default () => {
  const { formatMessage } = useIntl();

  return (
    <>
      <Form.Item
        name={['config', 'github', 'repo']}
        rules={[
          {
            required: true,
            message: formatMessage({ id: 'github.repo.required' }),
          },
        ]}
        label={formatMessage({ id: 'github.repo' })}
      >
        <Input placeholder={formatMessage({ id: 'github.repo' })} />
      </Form.Item>
      <Form.Item
        name={['config', 'github', 'branch']}
        rules={[
          {
            required: true,
            message: formatMessage({ id: 'github.branch.required' }),
          },
        ]}
        label={formatMessage({ id: 'github.branch' })}
      >
        <Input placeholder={formatMessage({ id: 'github.branch' })} />
      </Form.Item>
      <Form.Item
        name={['config', 'github', 'path']}
        rules={[
          {
            required: true,
            message: formatMessage({ id: 'github.path.required' }),
          },
        ]}
        label={formatMessage({ id: 'github.path' })}
      >
        <Input placeholder={formatMessage({ id: 'github.path' })} />
      </Form.Item>
    </>
  );
};
