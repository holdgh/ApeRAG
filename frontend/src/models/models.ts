import { ModelConfig, ModelDefinition, PromptTemplate } from '@/api';
import { api } from '@/services';
import { useEffect, useState } from 'react';
import { useModel } from 'umi';

export default () => {
  const { setLoading } = useModel('global');
  const { user } = useModel('user');
  const [promptTemplates, setPromptTemplates] = useState<PromptTemplate[]>();
  const [availableModels, setAvailableModels] = useState<ModelConfig[]>([]);

  // get available models
  const getAvailableModels = async () => {
    setLoading(true);
    const res = await api.availableModelsGet();
    setLoading(false);
    setAvailableModels(res.data.items || []);
  };

  const getProviderByModelName = (
    name: string = '',
    type: 'embedding' | 'completion' | 'rerank',
  ): { provider?: ModelConfig; model?: ModelDefinition } => {
    let provider;
    let model;
    availableModels.forEach((p) => {
      p[type]?.forEach((m) => {
        if (m.model === name) {
          provider = p;
          model = m;
        }
      });
    });
    return { provider, model };
  };

  // prompt templates
  const getPromptTemplates = async () => {
    setLoading(true);
    const res = await api.promptTemplatesGet();
    setLoading(false);
    setPromptTemplates(res.data.items);
  };

  useEffect(() => {
    if (user) getAvailableModels();
  }, [user]);

  return {
    promptTemplates,
    getPromptTemplates,
    setPromptTemplates,

    availableModels,
    getProviderByModelName,
  };
};
