import { Bot } from '@/api';
import { Merge } from './tool';

export type BotConfig = {
  model?: string;
  chractor?: string;
  llm?: {
    endpoint?: string;
    similarity_score_threshold?: number;
    similarity_topk?: number;
    context_window?: number;
    prompt_template?: string;
    temperature?: number;
    memory_prompt_template: string;
  };
  memory: boolean;
  use_related_question: boolean;
  feishu?: {
    encrypt_key?: string;
  };
};

export type ApeBot = Merge<
  Bot,
  {
    config?: BotConfig;
  }
>;
