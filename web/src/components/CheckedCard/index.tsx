import { Avatar, Card, Col, Row, Space, Typography } from 'antd';
import { ReactNode, useEffect, useState } from 'react';

import classNames from 'classnames';
import styles from './index.less';

type OptionType = {
  icon?: ReactNode;
  label: ReactNode;
  value: string;
  description?: string;
  disabled?: boolean;
};
type PropsType = {
  value?: string;
  defaultValue?: string;
  onChange?: (str: string, record: any) => void;
  options?: OptionType[];
  disabled?: boolean;
  block?: boolean;
  size?: 'middle' | 'large';
};

export default ({
  value,
  defaultValue,
  onChange = () => {},
  options = [],
  disabled,
  block = false,
}: PropsType) => {
  const [currentValue, setCurrentValue] = useState<string | undefined>(
    value || defaultValue,
  );
  // const { token } = theme.useToken();
  const onClick = (record: OptionType) => {
    if (disabled || record.disabled) return;
    setCurrentValue(record.value);
    onChange(record.value, record);
  };

  useEffect(() => {
    setCurrentValue(value);
  }, [value]);

  const blockLayout = {
    span: 24,
  };

  const inlineLayout = {
    xs: 24,
    sm: 24,
    md: 24,
    lg: 12,
    xl: 8,
    xxl: 8,
  };
  const layout = block ? blockLayout : inlineLayout;

  return (
    <Row gutter={[16, 16]}>
      {options.map((option, key) => (
        <Col key={key} {...layout}>
          <Card
            className={classNames({
              [styles.item]: true,
              [styles.selected]: currentValue === option.value,
              [styles.disabled]: disabled || option.disabled,
            })}
            bodyStyle={{
              padding: '16px 20px',
              borderRadius: '8px',
            }}
            onClick={() => {
              onClick(option);
            }}
          >
            <Space className={styles.row}>
              <Space style={{ flex: 1 }} size={'middle'}>
                {option.icon ? <Avatar size={32} src={option.icon} /> : null}
                <Space direction="vertical" style={{ flex: 1 }}>
                  <Typography.Text
                    type={disabled || option.disabled ? 'secondary' : undefined}
                  >
                    {option.label}
                  </Typography.Text>
                  {option.description ? (
                    <Typography.Text type="secondary" ellipsis>
                      {option.description}
                    </Typography.Text>
                  ) : null}
                </Space>
              </Space>
            </Space>
          </Card>
        </Col>
      ))}
    </Row>
  );
};
