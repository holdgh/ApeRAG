export const model = {
  'model.name': '模型',
  'model.required': '请选择模型',
  'model.config': '模型配置',
  'model.prompt_template': '提示模版',
  'model.prompt_template.default': `你是一个根据对话记录和候选答案来回答问题的专家，你的回答严格限定于刚才的对话记录和下面给你提供的候选答案。
你需要基于刚才的对话记录，谨慎准确的依据markdown格式的候选答案，来回答问题：{query}。
请一步一步思考，请确保回答准确和简洁，如果从对话记录和候选答案中找不出回答，就直接说你不知道，不要试图编造一个回答。
问题只回答一次。
候选答案如下:
----------------
{context}
----------------`,
  'model.llm.tips': '大型语言对话模型',
  'model.rerank.tips':
    '在拿到向量查询（ANN）的结果后使用 Reranker，能够更有效地确定文档和查询之间的语义相关性，更精细地对结果重排，最终提高搜索质量。',
  'model.llm_params': 'LLM 参数',
  'model.llm_context_window': '上下文窗口',
  'model.llm_context_window_required': '上下文窗口为必填项',
  'model.llm_similarity_score_threshold': '相似度阈值',
  'model.llm_similarity_score_threshold_required': '请输入相似度阈值',
  'model.llm_similarity_topk': 'Top-K 取值',
  'model.llm_similarity_topk_required': '请输入Top-K',
  'model.llm_temperature': '温度',
  'model.llm_temperature_required': '请输入温度',
  'model.memory': '上下文记忆',
  'model.memory_tips': '(是否参考历史对话记录，开启后会增加模型调用成本)',
  'model.memory_max_token': '上下文字数',
  'model.memory_max_session': '上下文条数',
  'model.memory_should_integer': '需要大于 0 的整数',
  'model.recall': '关键词召回',
  'model.recall_help':
    '如果关联的文档集包含的文档数量少于 200 篇，建议开启此选项',
  'model.use_related_question': '启用相关问题',
  'model.related_question_prompt': '你可以继续这样问我',
  'model.related_question_tips': '相关问题提示语',
  'model.related_prompt_template': '生成相关问题提示模版',
  'model.provider': '模型服务商',
  'model.provider.description': '设置模型服务商的服务URI及API Key',
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
