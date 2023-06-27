import _ from 'lodash';

const collections = [
  {
    id: 1,
    title: 'Kubeblocks user manual',
    status: 'ACTIVE',
    type: 'document',
    description:
      'This collection is designed to provided documents for kubeblocks who are interested in learning the kubeblocks, database and gitops.',
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
const chats = [
  {
    id: 1,
    collection: collections[0],
    history: [
      {
        role: 'human',
        message: 'Hi',
      },
      {
        role: 'robot',
        message: 'Hi',
      },
    ],
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
      data: chats,
    });
  },
  'POST /api/v1/collections/:collectionId/chats': (req: any, res: any) => {
    res.json({
      data: chats[0],
    });
  },
};
