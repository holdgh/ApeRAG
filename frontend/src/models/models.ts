import { PromptTemplate } from '@/api';
import { api } from '@/services';
import { useState } from 'react';
import { useModel } from 'umi';

export default () => {
  const { setLoading } = useModel('global');
  const [promptTemplates, setPromptTemplates] = useState<PromptTemplate[]>();

  // prompt templates
  const getPromptTemplates = async () => {
    setLoading(true);
    const res = await api.promptTemplatesGet();
    setLoading(false);
    setPromptTemplates(res.data.items);
  };

  return {
    promptTemplates,
    getPromptTemplates,
    setPromptTemplates,
  };
};
