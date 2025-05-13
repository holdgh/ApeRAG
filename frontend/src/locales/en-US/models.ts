export const model = {
  'model.name': 'Models',
  'model.required': 'Model is required',
  'model.config': 'Model Config',
  'model.prompt_template': 'Prompt Template',
  'model.llm.tips': 'Large language chat model',
  'model.rerank.tips':
    'Using Reranker after getting the results of a vector query (ANN) can more effectively determine the semantic relevance between documents and queries, re-rank the results more finely, and ultimately improve search quality.',
  'model.llm_params': 'LLM Params',
  'model.llm_context_window': 'Context Window',
  'model.llm_context_window_required': 'Context Window is required',
  'model.llm_similarity_score_threshold': 'Similarity Score Threshold',
  'model.llm_similarity_score_threshold_required':
    'Similarity Score Threshold is required',
  'model.llm_similarity_topk': 'Similarity Topk',
  'model.llm_similarity_topk_required': 'Similarity Topk is required',
  'model.llm_temperature': 'Temperature',
  'model.llm_temperature_required': 'Temperature is required',
  'model.memory': 'Context Memory',
  'model.memory_tips':
    ' ( Refers to historical dialogue records or not, the model call costs will increased when enabled )',
  'model.memory_max_token': 'Context Tokens',
  'model.memory_max_session': 'Context Sessions',
  'model.memory_should_integer': 'Need an integer',
  'model.recall': 'Keyword Recall',
  'model.recall_help':
    'If the associated collections contains less than 200 documents, it is recommended to enable this option',
  'model.use_related_question': 'Enable related questions',
  'model.related_question_prompt': 'You can continue to ask me',
  'model.related_question_tips': 'Related questions prompt',
  'model.related_prompt_template': 'Related Questions Prompt Template',
};

export const model_provider = {
  'model.provider': 'Model Provider',
  'model.provider.required': 'Model Provider is required',
  'model.provider.description':
    'Set the service URI and API Key of the model service provider',

  'model.provider.settings': 'Provider Settings',
  'model.provider.enable': 'Enable',
  'model.provider.disable': 'Disable',
  'model.provider.disable.confirm': 'Are you sure to disable {label} provider?',
  'model.provider.uri': 'Provider URI',
  'model.provider.uri.required': 'Provider URI is required',
  'model.provider.api_key': 'Provider API Key',
  'model.provider.api_key.required': 'Provider API Key is required',
  'model.provider.add': 'Add Provider',
};
