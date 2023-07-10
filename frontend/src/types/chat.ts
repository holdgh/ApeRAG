export type TypesSocketStatus =
  | 'Closed'
  | 'Open'
  | 'Connecting'
  | 'Closing'
  | 'Uninstantiated';
export type TypesMessageType = 'start' | 'stop' | 'message' | 'sql' | 'error' | 'finish';
export type TypesChatStatus = 'finish';
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
  collectionId: string;
  summary: string;
  history: TypesMessage[];
  status: TypesChatStatus,
  created: string;
  updated: string;
};
