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
      }}
    >
      <ProConfigProvider dark={true}>
        <App>
          {children}
          {/* <div style={{ maxWidth: 1480, margin: '0 auto' }}>{children}</div> */}
        </App>
      </ProConfigProvider>
    </ConfigProvider>
  );
};
