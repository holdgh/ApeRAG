import { GetModels, GetChractors } from '@/services/model';
import { TypesModels } from '@/types';
import _ from 'lodash';
import { useState } from 'react';

export default () => {
  const [models, setModels] = useState<TypesModels[]>([]);
  const [chractors, setChractors] = useState<any>();

  const getModels = async () => {
    if (_.isEmpty(models)) {
      const { data } = await GetModels();
      setModels(data);
    }
  };

  const getChractors = async () => {
    if (_.isEmpty(chractors)) {
      const { data } = await GetChractors();
      setChractors(data);
    }
  };

  return {
    models,
    chractors,
    getModels,
    getChractors,
  };
};
