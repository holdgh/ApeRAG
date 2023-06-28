import type { Collection } from './collection';

export type SocketStatus = 'Closed' | 'Connected' | 'Connecting';
export type MessageStatus = 'loading' | 'error' | 'normal';

export type Message = {
  type?: 'ping' | 'pong' | 'message';
  role?: 'ai' | 'human';
  code?: '200' | '500';
  data?: string;
  error?: string;
  timestamp?: string;
  references?: string;
};

export type Chat = {
  id: number;
  name: string;
  user: string;
  collection: Collection;
  history: Message[];
  created: string;
  updated: string;
};

export default () => {
  return {};
};
