export type TypesSocketStatus =
  | 'Closed'
  | 'Open'
  | 'Connecting'
  | 'Closing'
  | 'Uninstantiated';
export type TypesMessageType =
  | 'welcome'
  | 'start'
  | 'stop'
  | 'message'
  | 'sql'
  | 'error'
  | 'download';
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
  upvote?: number;
  downvote?: number;
  revised_answer?: string;
  _original_answer?: string;
  _typeWriter?: boolean;
};

export type TypesChat = {
  id: string;
  bot_id: string;
  summary: string;
  history: TypesMessage[];
  status: TypesChatStatus;
  created: string;
  updated: string;
};
