import type { Collection } from './collection';

export type ChatSocketStatus = 'Closed' | 'Connected' | 'Connecting';

export type ChatHistory = {
  role: 'robot' | 'human';
  message: string;
};

export type Chat = {
  id: number;
  name: string;
  user: string;
  collection: Collection;
  history: ChatHistory[];
  gmt_created: string;
  gmt_updated: string;
  gmt_deleted: string;
};

export default () => {
  return {};
};
