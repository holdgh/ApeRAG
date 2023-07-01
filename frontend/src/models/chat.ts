import type { Collection } from './collection';

export type SocketStatus =
  | 'Closed'
  | 'Open'
  | 'Connecting'
  | 'Closing'
  | 'Uninstantiated';
export type MessageType = 'message' | 'stop' | 'error' | 'sql';
export type MessageRole = 'ai' | 'human';

export type Message = {
  type?: MessageType;
  role?: MessageRole;
  data?: string;
  timestamp?: number;
  references?: string;
};

export type Chat = {
  id: string;
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
