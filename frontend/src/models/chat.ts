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
  created: string;
  updated: string;
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
