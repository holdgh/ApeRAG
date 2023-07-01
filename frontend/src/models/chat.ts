import type { TypesCollection } from './collection';

export type TypesSocketStatus =
  | 'Closed'
  | 'Open'
  | 'Connecting'
  | 'Closing'
  | 'Uninstantiated';
export type TypesMessageType = 'message' | 'stop' | 'error' | 'sql';
export type TypesMessageRole = 'ai' | 'human';

export type TypesMessage = {
  type?: TypesMessageType;
  role?: TypesMessageRole;
  data?: string;
  timestamp?: number;
  references?: string;
};

export type TypesChat = {
  id: string;
  name: string;
  user: string;
  collection: TypesCollection;
  history: TypesMessage[];
  created: string;
  updated: string;
};

export default () => {
  return {};
};
