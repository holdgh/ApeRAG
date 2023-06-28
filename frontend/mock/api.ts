import fs from 'fs';
import _ from 'lodash';
import path from 'path';

const collections = [
  {
    id: 1,
    title: 'Kubeblocks user manual',
    status: 'ACTIVE',
    type: 'document',
    description: 'This collection is designed to provided documents',
  },
  {
    id: 2,
    title: 'Sealos user manual',
    status: 'INACTIVE',
    type: 'document',
    description:
      'This collection is designed to provided documents for kubeblocks who are interested in learning the kubeblocks, database and gitops.',
  },
  {
    id: 3,
    title: 'Kubeblocks user manual',
    status: 'ACTIVE',
    type: 'document',
    description:
      'This collection is designed to provided documents for kubeblocks who are interested in learning the kubeblocks, database and gitops.',
  },
  {
    id: 4,
    title: 'Sealos user manual',
    status: 'INACTIVE',
    type: 'multimedia',
    description:
      'This collection is designed to provided documents for kubeblocks who are interested in learning the kubeblocks, database and gitops.',
  },
];
const documents = [
  {
    id: 1,
    name: 'Kubeblocks user manual(1/4).pdf',
    status: 'COMPLETE',
    size: 85,
    updatedAt: '2023-06-27T07:58:06.274709+00:00',
  },
  {
    id: 2,
    name: 'Kubeblocks user manual(2/4).pdf',
    status: 'FAILED',
    size: 85,
    updatedAt: '2023-06-27T07:58:06.274709+00:00',
  },
  {
    id: 3,
    name: 'Kubeblocks user manual(3/4).pdf',
    status: 'FAILED',
    size: 85,
    updatedAt: '2023-06-27T07:58:06.274709+00:00',
  },
  {
    id: 4,
    name: 'Kubeblocks user manual(4/4).pdf',
    status: 'COMPLETE',
    size: 85,
    updatedAt: '2023-06-27T07:58:06.274709+00:00',
  },
];

export default {
  // collections
  'GET /api/v1/collections': (req: any, res: any) => {
    res.json({ data: collections });
  },
  'POST /api/v1/collections': (req: any, res: any) => {
    res.json({
      data: {
        id: _.random(10, 1000),
        status: 'InActive',
        ...req.body,
      },
    });
  },
  'GET /api/v1/collections/:collectionId': (req: any, res: any) => {
    res.json({
      data: { ...collections[0], id: req.params.collectionId },
    });
  },
  'PUT /api/v1/collections/:collectionId': (req: any, res: any) => {
    res.json({
      data: req.body,
    });
  },

  // documents
  'GET /api/v1/collections/:collectionId/documents': (req: any, res: any) => {
    res.json({
      data: documents,
    });
  },
  'POST /api/v1/collections/:collectionId/documents': (req: any, res: any) => {
    res.json({
      data: documents[0],
    });
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
          id: _.random(1, 1000),
        },
      ],
    });
  },
  'GET /api/v1/collections/:collectionId/chats/:chatId': (
    req: any,
    res: any,
  ) => {
    res.json({
      data: {
        id: req.params.chatId,
        collection: collections.find(
          (c) => String(c.id) === req.params.collectionId,
        ),
        history: [
          {
            type: 'message',
            role: 'human',
            timestamp: "1687936930307",
            data: `what is kubeblocks?`,
          },
          {
            role: 'ai',
            type: 'message',
            timestamp: "1687936930307",
            data: String(
              fs.readFileSync(path.join(__dirname, './example_markdown.md')),
            ),
          },
          {
            role: 'human',
            type: 'message',
            timestamp: "1687936930307",
            data: `describe cluster with kbcli...`,
          },
          {
            role: 'ai',
            type: 'message',
            timestamp: "1687936930307",
            data: String(
              fs.readFileSync(path.join(__dirname, './example_kbcli.md')),
            ),
          },
          {
            role: 'human',
            type: 'message',
            timestamp: "1687936930307",
            data: `sql example...`,
          },
          {
            role: 'ai',
            type: 'message',
            timestamp: "1687936930307",
            data: String(
              fs.readFileSync(path.join(__dirname, './example_sql.md')),
            ),
          },
        ],
      },
    });
  },
  'POST /api/v1/collections/:collectionId/chats': (req: any, res: any) => {
    res.json({
      data: {
        id: _.random(1, 1000),
        collection: collections.find(
          (c) => String(c.id) === req.params.collectionId,
        ),
        history: [],
      },
    });
  },
  'PUT /api/v1/collections/:collectionId/chats/:chatId': (
    req: any,
    res: any,
  ) => {
    res.json({
      data: {
        id: parseInt(req.params.chatId),
        collection: collections.find(
          (c) => String(c.id) === req.params.collectionId,
        ),
        history: [],
      },
    });
  },
};
