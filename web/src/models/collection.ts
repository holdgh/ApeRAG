import {
  CreateCollection,
  DeleteCollection,
  GetCollections,
  GetDefaultCollections,
  UpdateCollection,
  GetRelatedQuestions,
  GetQuestionDetails,
  GenRelatedQuestions,
  UpdateRelatedQuestion,
  DeleteRelatedQuestion,
} from '@/services/collections';

import type { TypesCollection, TypesCollectionConfig } from '@/types';
import { parseConfig, stringifyConfig } from '@/utils/configParse';
import { history } from '@umijs/max';
import { App } from 'antd';
import _ from 'lodash';
import { useState } from 'react';

export default () => {
  const [collections, setCollections] = useState<TypesCollection[]>();
  const [collectionLoading, setCollectionLoading] = useState<boolean>(false);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [totalQuestions, setTotalQuestions] = useState<number>(0);
  const [questionGenerating, setQuestionGenerating] = useState<boolean>(false);
  const [questions, setQuestions] = useState<any>();
  const [questionsLoading, setQuestionsLoading] = useState<boolean>(false);
  const { message } = App.useApp();

  const getCollections = async (pagenumber, pagesize) => {
    setCollectionLoading(true);

    const collectionsRes = await GetCollections(pagenumber, pagesize);

    // const [collectionsRes, defaultCollectionsRes] = await Promise.all([
    //   GetCollections(pagenumber, pagesize),
    //   GetDefaultCollections(pagenumber, pagesize),
    // ]);

    collectionsRes?.data.forEach((d) => {
      // d.system = false;
      d.config = parseConfig(d.config as string);
    });

    // defaultCollectionsRes?.data.forEach((d) => {
    //   d.system = true;
    //   d.config = parseConfig(d.config as string);
    // });

    const collection = collectionsRes;
    // const collection = collectionsRes?.data?.length>0 ? collectionsRes : defaultCollectionsRes;

    setCollections(collection.data);
    setTotalCount(collection.count||collection.data?.length||0);
    setCollectionLoading(false);
  };

  const getQuestions = async (collectionId?: String, pagenumber?: number, pagesize?:number) => {
    setQuestionsLoading(true);
    const questions = await GetRelatedQuestions(collectionId, pagenumber, pagesize);
    setQuestions(questions.data);
    setQuestionGenerating(questions.question_status==='PENDING');
    setTotalQuestions(questions.count||questions.data?.length||0);
    setQuestionsLoading(false);
  }

  const getCollection = (id?: string): TypesCollection | undefined => {
    if (!id) return;
    const data = collections?.find((c) => String(c.id) === String(id));
    return data;
  };

  const deleteCollection = async (collection?: TypesCollection) => {
    if (!collections || !collection?.id) return;
    const { code } = await DeleteCollection(collection.id);
    if (code === '200') {
      setCollections(collections.filter((c) => c.id !== collection.id));
      setTimeout(() => history.push(`/collections`));
    }
  };

  const createColection = async (params: TypesCollection) => {
    setCollectionLoading(true);

    params.config = stringifyConfig(params.config) as TypesCollectionConfig;
    const { data, code } = await CreateCollection(params);
    setCollectionLoading(false);
    if (code === '200') {
      message.success('Created successfully');
      data.config = parseConfig(data.config as string);
      await setCollections(collections?.concat(data));
      history.push(`/collections`);
    }
  };

  const updateCollection = async (
    collectionId: string,
    params: TypesCollection,
  ) => {
    setCollectionLoading(true);
    const { data, code } = await UpdateCollection(collectionId, {
      ...params,
      config: stringifyConfig(params.config) as TypesCollectionConfig,
    });

    setCollectionLoading(false);

    if (code === '200') {
      message.success('Update completed');
      data.config = parseConfig(data.config as string);
      const index = collections?.findIndex((c) => c.id === collectionId);
      if (index !== -1 && collections?.length && index !== undefined) {
        _.update(collections, index, (origin) => {
          return {
            ...origin,
            ...data,
          };
        });
        setCollections(collections);
      }
    }
  };

  return {
    collections,
    totalCount,
    collectionLoading,
    questions,
    totalQuestions,
    questionGenerating,
    questionsLoading,
    setQuestions,
    getCollections,
    setCollections,
    getCollection,
    deleteCollection,
    createColection,
    updateCollection,
    getQuestions,
    GetQuestionDetails,
    GenRelatedQuestions,
    UpdateRelatedQuestion,
    DeleteRelatedQuestion,
  };
};
