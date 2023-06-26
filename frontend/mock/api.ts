const collections = [
  {
    id: 1,
    title: 'Kubeblocks user manual',
    status: 'Active',
    type: 'Document',
    description:
      'This collection is designed to provided documents for kubeblocks who are interested in learning the kubeblocks, database and gitops.',
  },
  {
    id: 2,
    title: 'Sealos user manual',
    status: 'InActive',
    type: 'Document',
    description:
      'This collection is designed to provided documents for kubeblocks who are interested in learning the kubeblocks, database and gitops.',
  },
  {
    id: 3,
    title: 'Kubeblocks user manual',
    status: 'Active',
    type: 'Document',
    description:
      'This collection is designed to provided documents for kubeblocks who are interested in learning the kubeblocks, database and gitops.',
  },
  {
    id: 4,
    title: 'Sealos user manual',
    status: 'InActive',
    type: 'Multimedia',
    description:
      'This collection is designed to provided documents for kubeblocks who are interested in learning the kubeblocks, database and gitops.',
  },
];
const documents = [
  {
    id: 1,
    name: 'Kubeblocks user manual(1/4).pdf',
    status: 'Complate',
    size: '15kb',
    updatedAt: '1687744191291',
  },
  {
    id: 2,
    name: 'Kubeblocks user manual(2/4).pdf',
    status: 'Failed',
    size: '15kb',
    updatedAt: '1687744191291',
  },
  {
    id: 3,
    name: 'Kubeblocks user manual(3/4).pdf',
    status: 'Failed',
    size: '15kb',
    updatedAt: '1687744191291',
  },
  {
    id: 4,
    name: 'Kubeblocks user manual(4/4).pdf',
    status: 'Complate',
    size: '15kb',
    updatedAt: '1687744191291',
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
        id: 8,
        status: 'InActive',
        ...req.body,
      },
    });
  },
  'GET /api/v1/collections/:collectionId': (req: any, res: any) => {
    res.json({
      data: collections.find((c) => c.id === parseInt(req.params.collectionId)),
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
  'DELETE /api/v1/collections/:collectionId/documents/:documentId': (
    req: any,
    res: any,
  ) => {
    res.json({
      data: req.params.documentId,
    });
  },
};
