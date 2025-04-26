import { ArrowLeftOutlined } from '@ant-design/icons';
import { Button, Space, Tooltip, Typography } from 'antd';
import { Link, useIntl } from 'umi';
import styles from './index.less';

export const PageHeader = ({
  title,
  backto,
  subTitle,
  children,
  description,
}: {
  title?: React.ReactNode;
  backto?: string;
  subTitle?: React.ReactNode;
  children?: React.ReactNode;
  description?: React.ReactNode;
}) => {
  const { formatMessage } = useIntl();
  return (
    <div className={styles.header}>
      <div className={styles.info}>
        {backto && (
          <Link to={backto} className={styles.backto}>
            <Tooltip title={formatMessage({ id: 'action.back' })}>
              <Button type="text" icon={<ArrowLeftOutlined />} />
            </Tooltip>
          </Link>
        )}
        <div>
          <div>
            <Space align="end">
              {typeof title === 'string' ? (
                <Typography.Title level={3} style={{ margin: 0 }}>
                  {title}
                </Typography.Title>
              ) : (
                title
              )}
              {typeof subTitle === 'string' ? (
                <Typography.Text type="secondary">{subTitle}</Typography.Text>
              ) : (
                subTitle
              )}
            </Space>
          </div>
          <div>
            {typeof description === 'string' ? (
              <Typography.Text type="secondary">{description}</Typography.Text>
            ) : (
              description
            )}
          </div>
        </div>
      </div>
      <div className={styles.content}>{children}</div>
    </div>
  );
};
