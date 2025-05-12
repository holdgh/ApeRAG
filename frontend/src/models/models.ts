import { ModelConfig, PromptTemplate } from '@/api';
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
  };
};
