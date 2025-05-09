import { ApeNodeType } from '@/types';

import { ApeNodeGlobal } from './_node_global';
import { ApeNodeKeywordSearch } from './_node_keyword_search';
import { ApeNodeLlm } from './_node_llm';
import { ApeNodeMerge } from './_node_merge';
import { ApeNodeRerank } from './_node_rerank';
import { ApeNodeVectorSearch } from './_node_vector_search';

export const NodeTypes: { [key in ApeNodeType]: any } = {
  global: ApeNodeGlobal,
  vector_search: ApeNodeVectorSearch,
  keyword_search: ApeNodeKeywordSearch,
  merge: ApeNodeMerge,
  rerank: ApeNodeRerank,
  llm: ApeNodeLlm,
};
