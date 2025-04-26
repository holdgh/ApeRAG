import { Model, PromptTemplate } from '@/api';
import { api } from '@/services';
import { useEffect, useState } from 'react';
import { useModel } from 'umi';

export default () => {
  const { user } = useModel('user');
  const { setLoading } = useModel('global');

  const [models, setModels] = useState<Model[]>();
  const [promptTemplates, setPromptTemplates] = useState<PromptTemplate[]>();

  // models
  const getModels = async () => {
    setLoading(true);

    const res = await api.modelsGet();
    setLoading(false);
    setModels(res.data.items);
  };

  // prompt templates
  const getPromptTemplates = async () => {
    setLoading(true);
    const res = await api.promptTemplatesGet();
    setLoading(false);
    setPromptTemplates(res.data.items);
  };

  useEffect(() => {
    if (user) {
      getModels();
    }
  }, [user]);

  return {
    models,
    getModels,
    setModels,

    promptTemplates,
    getPromptTemplates,
    setPromptTemplates,
  };
};
