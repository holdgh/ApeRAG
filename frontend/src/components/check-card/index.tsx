import { Avatar, Card, Col, Row, Space, theme, Typography } from 'antd';
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
};

export const CheckCard = ({
  value,
  defaultValue,
  onChange = () => {},
  options = [],
  disabled,
  block = false,
}: PropsType) => {
  const { token } = theme.useToken();
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
    sm: 12,
    md: 8,
    lg: 6,
    xl: 4,
    xxl: 4,
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
            styles={{
              body: {
                padding: '8px 12px',
                borderRadius: token.borderRadius,
              },
            }}
            onClick={() => {
              onClick(option);
            }}
          >
            <Space className={styles.row}>
              <Space style={{ flex: 1 }}>
                {option.icon ? (
                  <Avatar shape="square" size={32} src={option.icon} />
                ) : null}
                <Space direction="vertical" style={{ flex: 1 }}>
                  <Typography.Text disabled={disabled || option.disabled}>
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
