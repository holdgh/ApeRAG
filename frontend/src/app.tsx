import { AntdConfig, RuntimeConfig } from 'umi';

export const antd: RuntimeConfig['antd'] = (antdConfig: AntdConfig) => {
  return antdConfig;
};

export const rootContainer = (container: JSX.Element) => {
  return container;
};
