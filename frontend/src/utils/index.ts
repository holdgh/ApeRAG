export const parseConfig = (str?: string) => {
  let result;
  try {
    result = JSON.parse(str || '');
  } catch (err) {
    result = {};
  }
  return result;
};

export const stringifyConfig = (conf?: any): string => {
  let result = '';
  try {
    result = JSON.stringify(conf);
  } catch (err) {
    result = '';
  }
  return result;
};
