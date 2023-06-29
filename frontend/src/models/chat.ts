import type { Collection } from './collection';

export type SocketStatus = 'Closed' | 'Connected' | 'Connecting';
export type MessageType = 'ping' | 'pong' | 'message' | 'stop' | 'error';
export type MessageRole = 'ai' | 'human';

export type Message = {
  type?: MessageType;
  role?: MessageRole;
  data?: string;
  timestamp?: number;
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
