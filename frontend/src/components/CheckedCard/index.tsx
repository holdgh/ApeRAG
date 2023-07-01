import { CheckOutlined } from '@ant-design/icons';
import { Avatar, Card, Col, Row, Space, Typography, theme } from 'antd';
import { ReactNode, useEffect, useState } from 'react';

import classNames from 'classnames';
import styles from './index.less';

type OptionType = {
  icon?: ReactNode;
  label: ReactNode;
  value: string;
  description?: string;
};
type PropsType = {
  value?: string;
  defaultValue?: string;
  onChange?: (str: string, record: any) => void;
  options?: OptionType[];
  disabled?: boolean;
};

export default ({
  value,
  defaultValue,
  onChange = () => {},
  options = [],
  disabled,
}: PropsType) => {
  const [currentValue, setCurrentValue] = useState<string | undefined>(
    value || defaultValue,
  );
  const { token } = theme.useToken();
  const onClick = (record: OptionType) => {
    if (disabled) return;
    setCurrentValue(record.value);
    onChange(record.value, record);
  };

  useEffect(() => {
    setCurrentValue(value);
  }, [value]);

  return (
    <Row gutter={[30, 30]}>
      {options.map((option, key) => (
        <Col key={key} xs={24} sm={24} md={24} lg={12} xl={12} xxl={12}>
          <Card
            className={classNames({
              [styles.item]: true,
              [styles.selected]: currentValue === option.value,
              [styles.disabled]: disabled,
            })}
            bodyStyle={{
              minHeight: 30,
              padding: '12px 20px',
            }}
            onClick={() => {
              onClick(option);
            }}
          >
            <Space className={styles.row}>
              <Space size="large" style={{ flex: 1 }}>
                {option.icon ? (
                  <Avatar style={{ fontSize: 24 }} size={50}>
                    {option.icon}
                  </Avatar>
                ) : null}
                <Space direction="vertical" style={{ flex: 1 }}>
                  <Typography.Text>{option.label}</Typography.Text>
                  {option.description ? (
                    <Typography.Text type="secondary" ellipsis>
                      {option.description}
                    </Typography.Text>
                  ) : null}
                </Space>
              </Space>
              <CheckOutlined
                className={styles.icon}
                style={{ color: token.colorPrimary }}
              />
            </Space>
          </Card>
        </Col>
      ))}
    </Row>
  );
};
