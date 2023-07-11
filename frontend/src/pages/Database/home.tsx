import { TypesCollectionType } from '@/types';
import { history, useModel } from '@umijs/max';
import _ from 'lodash';
import { useEffect } from 'react';

export default () => {
  const { currentCollection, collections, setCurrentCollection } =
    useModel('collection');
  const { currentChat } = useModel('chat');
  useEffect(() => {
    if (!currentCollection?.id || !currentChat?.id) return;

    const type: TypesCollectionType = 'database';
    const first = _.first(collections?.filter((c) => c.type === type));
    if (currentCollection?.type === type) {
      history.replace(`/${type}/${currentCollection.id}/chat`);
    } else if (first) {
      setCurrentCollection(first);
      history.replace(`/${type}/${first.id}/chat`);
    }
  }, []);

  return null;
};
