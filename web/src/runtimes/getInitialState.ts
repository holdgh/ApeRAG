import { getLocale } from '@umijs/max';
import moment from 'moment';

export type InitialStateType = {
  collapsed?: boolean;
};

export async function getInitialState(): Promise<InitialStateType> {
  const locale = getLocale();
  moment.locale(locale === 'en-US' ? 'en' : 'zh');

  return {};
}
