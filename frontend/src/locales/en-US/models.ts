export const model = {
  'model.name': 'Models',
  'model.prompt_template': 'Prompt Template',
  'model.llm.tips': 'Large language chat model',
  'model.rerank.tips':
    'Using Reranker after getting the results of a vector query (ANN) can more effectively determine the semantic relevance between documents and queries, re-rank the results more finely, and ultimately improve search quality.',
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
