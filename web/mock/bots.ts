import _ from 'lodash';
import mockjs from 'mockjs';

const BotMock = {
  id: '@id',
  title: '@title',
  description: '@sentence(3, 20)',
  status: /(ACTIVE|INACTIVE)/,
  config:
    '{"model": "vicuna-13b", "llm": {"prompt_template": "\n上下文信息如下:\n----------------\n\n{context}\n\n--------------------\n\n\n根据提供的上下文信息，请一步一步思考，然后回答问题：{query}。\n\n请确保回答准确和简洁。\n"}}',
};

export default {
  'GET /api/v1/bots': (req: any, res: any) => {
    res.json(
      mockjs.mock({
        success: true,
        'data|10': [BotMock],
      }),
    );
  },
  'GET /api/v1/bots/:botId': (req: any, res: any) => {
    res.json(
      mockjs.mock({
        data: { ...BotMock, id: req.params.botId },
      }),
    );
  },
  'POST /api/v1/bots': (req: any, res: any) => {
    res.json({
      data: {
        id: String(_.random(10, 1000)),
        ...req.body,
      },
    });
  },
  'PUT /api/v1/bots/:botId': (req: any, res: any) => {
    res.json({
      data: req.body,
    });
  },
};
