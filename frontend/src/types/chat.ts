export type TypesSocketStatus =
  | 'Closed'
  | 'Open'
  | 'Connecting'
  | 'Closing'
  | 'Uninstantiated';
export type TypesMessageType = 'start' | 'stop' | 'message' | 'sql' | 'error';
export type TypesMessageRole = 'ai' | 'human';

export type TypesMessageReferences = {
  score?: number;
  text?: string;
  metadata?: {
    source?: string;
  };
};

export type TypesMessage = {
  id?: string;
  type?: TypesMessageType;
  role?: TypesMessageRole;
  data?: string;
  timestamp?: number;
  references?: TypesMessageReferences[];
  _typeWriter?: boolean;
};

export type TypesChat = {
  id: string;
  summary: string;
  history: TypesMessage[];
  created: string;
  updated: string;
};
