import type { Collection } from './collection';

export type SocketStatus = 'Closed' | 'Connected' | 'Connecting';
export type MessageStatus = 'loading' | 'error' | 'normal';

export type Message = {
  type?: 'ping' | 'pong' | 'message';
  data?: string;
  timestamps?: string;
  references?: any[];
  code?: '200' | '500';
  error?: string;
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

export type ChatHistory = {
  role: 'robot' | 'human';
  message: string;
  timestamps?: string;
  references?: any[];
};

export default () => {
  return {};
};
