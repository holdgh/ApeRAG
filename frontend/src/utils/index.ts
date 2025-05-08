import { ModelConfig, ModelDefinition } from '@/api';
import { ThemeType } from 'ahooks/lib/useTheme';

/**
 * Parse string to json
 * @param str
 * @returns
 */
export const parseConfig = <T>(str?: string): T => {
  let result;
  try {
    result = JSON.parse(str || '');
  } catch (err) {
    result = {};
  }
  return result;
};

/**
 * Stringify config
 * @param conf
 * @returns
 */
export const stringifyConfig = <T>(conf?: T): string => {
  let result: string;
  try {
    result = JSON.stringify(conf);
  } catch (err) {
    result = '{}';
  }
  return result;
};

/**
 * Get logo by theme name
 * @param themeName
 * @returns
 */
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

/**
 * replace string by *****
 * @param str
 * @param start
 * @param end
 * @returns string
 */
export const sensitiveStringReplace = (
  str: string = '',
  start: number = 5,
  end: number = 10,
): string =>
  str.substring(0, start) + '*'.repeat(end - start) + str.substring(end);

/**
 * Get provider by model name
 * @param name
 * @param type
 * @param availableModels
 * @returns { provider: ModelConfig, model: ModelDefinition }
 */
export const getProviderByModelName = (
  name: string = '',
  type: 'embedding' | 'completion' | 'rerank',
  availableModels: ModelConfig[],
): { provider?: ModelConfig; model?: ModelDefinition } => {
  let provider;
  let model;

  availableModels.forEach((p) => {
    p[type]?.forEach((m) => {
      if (m.model === name) {
        provider = p;
        model = m;
      }
    });
  });
  return { provider, model };
};
