const collections = [
  {
    id: 'colcb4a1d13d23f7e79',
    title: 'KubeBlocks文档集',
    description: '',
    status: 'ACTIVE',
    type: 'document',
    bot_ids: [],
    system: false,
    config:
      '{"source": "system", "crontab": {"enabled": false, "minute": "0", "hour": "0", "day_of_month": "*", "month": "*", "day_of_week": "*"}, "embedding_model": "bge"}',
    created: '2025-04-12T15:24:02.157270+00:00',
    updated: '2025-04-12T15:24:02.505044+00:00',
  },
  {
    id: 'col3544125b631a1337',
    title: 'ApeCloud文档集',
    description: null,
    status: 'QUESTION_PENDING',
    type: 'document',
    bot_ids: [],
    system: false,
    config:
      '{"source":"system","crontab":{"enabled":false,"minute":"0","hour":"0","day_of_month":"*","month":"*","day_of_week":"*"},"embedding_model":"bge","sensitive_protect":true,"sensitive_protect_method":"replace"}',
    created: '2023-11-09T10:56:33.339629+00:00',
    updated: '2025-04-12T15:21:54.917737+00:00',
  },
];

export default {
  'GET /api/v1/collections': {
    code: '200',
    data: collections,
    page_number: 1,
    page_size: 10,
    count: 3,
  },
  'POST /api/v1/collections': {
    code: '200',
  },
  'GET /api/v1/collections/:collectionId': (req: any, res: any) => {
    const { params } = req;
    res.status(200).json({
      code: '200',
      data: collections.find(
        (collection) => collection.id === params.collectionId,
      ),
    });
  },
  'PUT /api/v1/collections/:collectionId': (req: any, res: any) => {
    res.status(200).json({
      code: '200',
      data: req.body,
    });
  },
  'DELETE /api/v1/collections/:collectionId': {
    code: '200',
  },
};
