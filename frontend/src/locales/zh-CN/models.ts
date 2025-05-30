export const model = {
  'model.name': '模型',
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
