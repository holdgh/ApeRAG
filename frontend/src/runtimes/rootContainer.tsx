import { ProConfigProvider } from '@ant-design/pro-provider';
import { App, ConfigProvider } from 'antd';
import React from 'react';

export const rootContainer = (children: React.ReactElement) => {
  return (
    <ConfigProvider
      theme={{
        token: {
          borderRadius: 4,
        },
        components: {
          Modal: {
            colorBgElevated: '#141414',
          },
          Form: {
            lineHeight: 1.2,
          },
          Descriptions: {
            titleMarginBottom: 8,
          },
        },
      }}
    >
      <ProConfigProvider dark={true}>
        <App>
        {children}
        </App>
      </ProConfigProvider>
    </ConfigProvider>
  );
};
