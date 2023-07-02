export type TypesSocketStatus =
  | 'Closed'
  | 'Open'
  | 'Connecting'
  | 'Closing'
  | 'Uninstantiated';
export type TypesMessageType = 'message' | 'stop' | 'error' | 'sql';
export type TypesMessageRole = 'ai' | 'human';

export type TypesMessageReferences = {
  score?: number;
  text?: string;
  metadata?: {
    source?: string;
  };
};

export type TypesMessage = {
  type?: TypesMessageType;
  role?: TypesMessageRole;
  data?: string;
  timestamp?: number;
  references?: TypesMessageReferences[];
};

export type TypesChat = {
  id: string;
  summary: string;
  history: TypesMessage[];
  created: string;
  updated: string;
};
