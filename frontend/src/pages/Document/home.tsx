import { TypesCollectionType } from '@/types';
import { history, useModel } from '@umijs/max';
import _ from 'lodash';
import { useEffect } from 'react';

export default () => {
  const { collections } = useModel('collection');

  useEffect(() => {
    const type: TypesCollectionType = 'document';
    const first = _.first(collections?.filter((c) => c.type === type));
    if (first) {
      history.replace(`/${type}/${first.id}/chat`);
    }
  }, []);

  return null;
};
