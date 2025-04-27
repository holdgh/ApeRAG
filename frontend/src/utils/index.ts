import { ThemeType } from 'ahooks/lib/useTheme';

export const parseConfig = <T>(str?: string): T => {
  let result;
  try {
    result = JSON.parse(str || '');
  } catch (err) {
    result = {};
  }
  return result;
};

export const stringifyConfig = <T>(conf?: T): string => {
  let result: string;
  try {
    result = JSON.stringify(conf);
  } catch (err) {
    result = '{}';
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

export const sensitiveStringReplace = (
  str: string = '',
  start: number = 5,
  end: number = 10,
): string =>
  str.substring(0, start) + '*'.repeat(end - start) + str.substring(end);
