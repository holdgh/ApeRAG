import { FormattedMessage } from '@umijs/max';
import { Modal, Typography } from 'antd';

export default () => {
  return (
    <Modal open={true} closable={false} width={600} footer={false}>
      <br />
      <br />
      <Typography.Title level={3} style={{ textAlign: 'center' }}>
        <FormattedMessage id="welcome" />
      </Typography.Title>

      <div style={{ margin: '40px 0', textAlign: 'center' }}>
        <Typography.Paragraph type="secondary" style={{ fontSize: 16 }}>
          <FormattedMessage id="welcome.email.confirm" />
        </Typography.Paragraph>
      </div>
    </Modal>
  );
};
