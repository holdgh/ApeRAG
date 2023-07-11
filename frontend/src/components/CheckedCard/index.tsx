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
  size = 'middle',
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

  const blockLayout = {
    span: 24,
  };

  const inlineLayout = {
    xs: 24,
    sm: 24,
    md: 12,
    lg: 8,
    xl: 8,
    xxl: 6,
  };
  const layout = block ? blockLayout : inlineLayout;

  return (
    <Row gutter={[8, 8]}>
      {options.map((option, key) => (
        <Col key={key} {...layout}>
          <Card
            className={classNames({
              [styles.item]: true,
              [styles.selected]: currentValue === option.value,
              [styles.disabled]: disabled,
            })}
            bodyStyle={{
              padding: size === 'middle' ? '8px 12px' : '12px 20px',
            }}
            onClick={() => {
              onClick(option);
            }}
          >
            <Space className={styles.row}>
              <Space
                style={{ flex: 1 }}
                size={size === 'middle' ? 'middle' : 'large'}
              >
                {option.icon ? (
                  <Avatar
                    style={{ fontSize: 24 }}
                    size={size === 'middle' ? 30 : 45}
                    src={option.icon}
                  />
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
