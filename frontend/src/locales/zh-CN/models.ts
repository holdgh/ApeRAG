export const model = {
  'model.name': '模型',
  'model.configuration': '模型配置',
  'model.prompt_template': '提示模版',
  'model.llm.tips': '大型语言对话模型',
  'model.rerank.tips':
    '在拿到向量查询（ANN）的结果后使用 Reranker，能够更有效地确定文档和查询之间的语义相关性，更精细地对结果重排，最终提高搜索质量。',
};

export const model_provider = {
  'model.provider': '模型服务商',
  'model.provider.required': '请选择模型服务商',
  'model.provider.description': '设置模型服务商的服务URI及API Key',

  'model.provider.settings': '服务商设置',
  'model.provider.enable': '启用',
  'model.provider.disable': '禁用',
  'model.provider.disable.confirm': '确定禁用 {label} 吗？',
  'model.provider.uri': '模型服务商 URI',
  'model.provider.uri.required': '请输入模型服务商URI',
  'model.provider.api_key': '模型服务商API Key',
  'model.provider.api_key.required': '请输入模型服务商API Key',
  'model.provider.add': '添加服务商',
};

export const model_configuration = {
  'model.configuration': '模型配置',
  'model.configuration.description': '配置LLM提供商和模型',
  
  // LLM Provider related
  'llm.provider': 'LLM提供商',
  'llm.provider.name': '提供商名称',
  'llm.provider.name.placeholder': '例如: openai',
  'llm.provider.label': '显示名称',
  'llm.provider.label.placeholder': '例如: OpenAI',
  'llm.provider.base_url': 'API基础URL',
  'llm.provider.base_url.placeholder': 'https://api.openai.com/v1',
  'llm.provider.allow_custom_base_url': '允许自定义URL',
  'llm.provider.completion_dialect': '对话API方言',
  'llm.provider.embedding_dialect': '嵌入API方言',
  'llm.provider.rerank_dialect': '重排API方言',
  'llm.provider.extra': '额外配置 (JSON)',
  'llm.provider.extra.placeholder': '{"key": "value"}',
  'llm.provider.add': '添加提供商',
  'llm.provider.edit': '编辑提供商',
  'llm.provider.delete.confirm': '确定要删除提供商 "{label}" 吗？这将同时删除该提供商下的所有模型。',
  
  // LLM Model related
  'llm.model': 'LLM模型',
  'llm.model.provider': '提供商',
  'llm.model.api_type': 'API类型',
  'llm.model.model_name': '模型名称',
  'llm.model.model_name.placeholder': '例如: gpt-4o-mini',
  'llm.model.custom_llm_provider': '自定义LLM提供商',
  'llm.model.custom_llm_provider.placeholder': '自动填充',
  'llm.model.max_tokens': '最大Token数',
  'llm.model.max_tokens.placeholder': '4096',
  'llm.model.tags': '标签',
  'llm.model.tags.placeholder': '输入标签',
  'llm.model.add': '添加模型',
  'llm.model.edit': '编辑模型',
  'llm.model.delete.confirm': '确定要删除模型 "{model}" 吗？',
  'llm.model.add.for.provider': '添加模型',
  
  // API types
  'llm.api.completion': 'Completion',
  'llm.api.embedding': 'Embedding',
  'llm.api.rerank': 'Rerank',
  
  // Form validation messages
  'llm.provider.name.required': '请输入提供商名称',
  'llm.provider.label.required': '请输入显示名称',
  'llm.provider.base_url.required': '请输入API基础URL',
  'llm.model.provider.required': '请选择提供商',
  'llm.model.api_type.required': '请选择API类型',
  'llm.model.model_name.required': '请输入模型名称',
  'llm.model.custom_llm_provider.required': '请输入自定义LLM提供商',
  
  // Success messages
  'llm.provider.created': '提供商创建成功',
  'llm.provider.updated': '提供商更新成功',
  'llm.provider.deleted': '提供商删除成功',
  'llm.model.created': '模型创建成功',
  'llm.model.updated': '模型更新成功',
  'llm.model.deleted': '模型删除成功',
  
  // Error messages
  'llm.configuration.fetch.error': '获取LLM配置失败',
  'llm.provider.save.error': '保存提供商失败',
  'llm.provider.delete.error': '删除提供商失败',
  'llm.model.save.error': '保存模型失败',
  'llm.model.delete.error': '删除模型失败',
};
