export const parseConfig = (configString: string): any => {
  const config = {};
  try {
    Object.assign(config, JSON.parse(configString));
  } catch (err) {}
  return config;
};

export const stringifyConfig = (config?: object): string => {
  let configString = '{}';
  try {
    configString = JSON.stringify(config);
  } catch (err) {}
  return configString;
};
