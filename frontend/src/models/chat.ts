import type { Collection } from './collection';

export type Chat = {
  name: string;
  user: string;
  collection: Collection;
  history: string;
  gmt_created: string;
  gmt_updated: string;
  gmt_deleted: string;
};

export default () => {
  return {};
};
