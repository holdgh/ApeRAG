import { CheckOutlined } from '@ant-design/icons';
import { Avatar, Card, Space, Typography, theme } from 'antd';
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
    <div>
      {options.map((option, key) => (
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
          key={key}
          onClick={() => {
            onClick(option);
          }}
          style={{
            borderColor:
              currentValue === option.value
                ? token.colorPrimary
                : token.colorBorder,
          }}
        >
          <Space className={styles.row}>
            <Space size="large">
              {option.icon ? (
                <Avatar style={{ fontSize: 24 }} size={50}>
                  {option.icon}
                </Avatar>
              ) : null}
              <Space direction="vertical">
                <Typography.Text>{option.label}</Typography.Text>
                {option.description ? (
                  <Typography.Text type="secondary">
                    {option.description}
                  </Typography.Text>
                ) : null}
              </Space>
            </Space>
            {currentValue === option.value ? (
              <Typography.Text type="success">
                <CheckOutlined className={styles.icon} />
              </Typography.Text>
            ) : null}
          </Space>
        </Card>
      ))}
    </div>
  );
};
