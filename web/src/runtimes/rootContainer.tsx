import { AuthProvider } from '@/components/Auth';
import { ProConfigProvider } from '@ant-design/pro-provider';
import { App, ConfigProvider } from 'antd';
import enUS from 'antd/locale/en_US';
import React from 'react';
import themeVariable from '@/variable';

export const rootContainer = (children: React.ReactElement) => {
  return (
    <AuthProvider>
      <ConfigProvider
        locale={enUS}
        theme={{
          token: {
            colorText: themeVariable.txtColorLight,
            colorPrimary: themeVariable.primaryColor,
            colorInfo: themeVariable.primaryColor,
            colorLink: themeVariable.primaryColor,
            colorLinkHover: themeVariable.txtHighlight,
            colorPrimaryHover: themeVariable.primaryColorLight,
            borderRadius: 8,
            borderRadiusLG: 16,
            controlItemBgActive: 'rgba(255, 255, 255, 0.08)',
            colorBgContainer: 'transparent',
            colorBgContainerDisabled: 'transparent',
            colorBgElevated:themeVariable.sidebarBackgroundColor,
            controlHeight: 40,
          },
          components: {
            Modal: {
              colorBgElevated: themeVariable.backgroundColor,
            },
            Form: {
              lineHeight: 1.2,
            },
            Descriptions: {
              titleMarginBottom: 8,
            },
            Select:{
              colorBgContainer: 'none',
            },
            Tabs:{
              itemSelectedColor: themeVariable.txtHighlight,
              itemHoverColor: themeVariable.txtHighlight,
              colorText: themeVariable.txtColor,
            },
          },
        }}
      >
        <ProConfigProvider dark={true}>
          <App>{children}</App>
        </ProConfigProvider>
      </ConfigProvider>
    </AuthProvider>
  );
};
