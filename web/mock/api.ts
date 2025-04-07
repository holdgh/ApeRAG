import _ from 'lodash';
import mockjs from 'mockjs';
import charExample from './chat_example.json';

// 数据mock示例：http://mockjs.com/examples.html

const CollectionMock = {
  id: '@id',
  title: '@title',
  status: /(ACTIVE|INACTIVE)/,
  type: '@email',
  config: '{"source": "email"}',
  description: '@sentence(3, 20)',
};

const DocumentMock = {
  id: '@id',
  name: '@title .@string(3)',
  status: /(COMPLETE|PENDING|RUNNING|FAILED|DELETED)/,
  size: '@integer(10, 1000000)',
  updatedAt: '@datetime',
};

const FeishuSpaceMock = {
  description: '@sentence(3, 20)',
  name: '@title',
  space_id: '@id',
  space_type: 'team',
  visibility: 'public',
};

const SyncHistoryMock = {
  id: '@id',
  total_documents: '@integer(10, 100)',
  new_documents: '@integer(10, 100)',
  deleted_documents: '@integer(10, 100)',
  processing_documents: '@integer(10, 100)',
  modified_documents: '@integer(10, 100)',
  failed_documents: '@integer(10, 100)',
  successful_documents: '@integer(10, 100)',
  start_time: '@datetime',
  execution_time: '@integer(10, 100)',
};

const ModelsMock = [
  {
    value: 'vicuna-13b',
    label: 'Vicuna 13b',
    enabled: true,
    prompt_template:
      '\n\u4e0a\u4e0b\u6587\u4fe1\u606f\u5982\u4e0b:\n----------------\n\n{context}\n\n--------------------\n\n\n\u6839\u636e\u63d0\u4f9b\u7684\u4e0a\u4e0b\u6587\u4fe1\u606f\uff0c\u8bf7\u4e00\u6b65\u4e00\u6b65\u601d\u8003\uff0c\u7136\u540e\u56de\u7b54\u95ee\u9898\uff1a{query}\u3002\n\n\u8bf7\u786e\u4fdd\u56de\u7b54\u51c6\u786e\u548c\u7b80\u6d01\u3002\n',
    context_window: 2000,
  },
  {
    value: 'baichuan-13b',
    label: 'BaiChuan 13b',
    enabled: true,
  },
  {
    value: 'chatglm2-6b',
    label: 'ChatGLM2 6b',
    enabled: false,
  },
  {
    value: 'chatgpt-3.5',
    label: 'ChatGPT 3.5',
    enabled: false,
  },
  {
    value: 'chatgpt-4',
    label: 'ChatGPT 4',
    enabled: false,
  },
];

export default {
  // feishu
  'GET /api/v1/feishu/spaces': (req: any, res: any) => {
    res.json(
      mockjs.mock({
        'data|10': [FeishuSpaceMock],
      }),
    );
  },

  // models
  'GET /api/v1/collections/models': (req: any, res: any) => {
    res.json({
      data: ModelsMock,
    });
  },

  // collections
  'GET /api/v1/collections': (req: any, res: any) => {
    res.json(
      mockjs.mock({
        success: true,
        'data|10': [CollectionMock],
      }),
    );
  },
  'POST /api/v1/collections': (req: any, res: any) => {
    res.json({
      data: {
        id: String(_.random(10, 1000)),
        status: 'InActive',
        ...req.body,
      },
    });
  },
  'GET /api/v1/collections/:collectionId': (req: any, res: any) => {
    res.json(
      mockjs.mock({
        data: { ...CollectionMock, id: req.params.collectionId },
      }),
    );
  },
  'PUT /api/v1/collections/:collectionId': (req: any, res: any) => {
    res.json({
      data: req.body,
    });
  },

  // documents
  'GET /api/v1/collections/:collectionId/documents': (req: any, res: any) => {
    res.json(
      mockjs.mock({
        'data|20': [DocumentMock],
      }),
    );
  },
  'POST /api/v1/collections/:collectionId/documents': (req: any, res: any) => {
    res.json(
      mockjs.mock({
        data: DocumentMock,
      }),
    );
  },
  'DELETE /api/v1/collections/:collectionId/documents/:documentId': (
    req: any,
    res: any,
  ) => {
    res.json({
      data: req.params.documentId,
    });
  },

  // chats
  'GET /api/v1/collections/:collectionId/chats': (req: any, res: any) => {
    res.json({
      data: [
        {
          id: String(_.random(1, 1000)),
        },
      ],
    });
  },
  'GET /api/v1/collections/:collectionId/chats/:chatId': (
    req: any,
    res: any,
  ) => {
    res.json(charExample);
  },
  'POST /api/v1/collections/:collectionId/chats': (req: any, res: any) => {
    res.json(
      mockjs.mock({
        data: {
          id: _.random(1, 1000),
          collection: CollectionMock,
          history: [],
        },
      }),
    );
  },
  'PUT /api/v1/collections/:collectionId/chats/:chatId': (
    req: any,
    res: any,
  ) => {
    res.json(
      mockjs.mock({
        data: {
          id: parseInt(req.params.chatId),
          collection: CollectionMock,
          history: [],
        },
      }),
    );
  },
  // sync
  'GET /api/v1/collections/:collectionId/sync/history': (
    req: any,
    res: any,
  ) => {
    res.json(
      mockjs.mock({
        'data|10': [SyncHistoryMock],
      }),
    );
  },
};
