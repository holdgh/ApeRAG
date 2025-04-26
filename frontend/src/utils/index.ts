import { ThemeType } from 'ahooks/lib/useTheme';

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

export const getLogo = (themeName: ThemeType) => {
  const defaultImgSrc = `${PUBLIC_PATH}logo_${themeName}.png`;
  switch (themeName) {
    case 'light':
      return APERAG_CONFIG.logo_light
        ? APERAG_CONFIG.logo_light
        : defaultImgSrc;
    case 'dark':
      return APERAG_CONFIG.logo_dark ? APERAG_CONFIG.logo_dark : defaultImgSrc;
  }
};
