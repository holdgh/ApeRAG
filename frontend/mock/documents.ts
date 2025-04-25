const documents = [
  {
    id: 'docf20b6eb49b0fa1b4',
    name: 'parameter-configuration.md',
    status: 'COMPLETE',
    config:
      '{"path": "/data/media/documents/user-auth0-65363df666d30473af5f30eb/col3544125b631a1337/parameter-configuration.md"}',
    size: 13933,
    created: '2023-12-13T05:56:09.085133+00:00',
    updated: '2023-12-13T05:56:58.948027+00:00',
    sensitive_info: [],
  },
  {
    id: 'doc137f19104a5cca37',
    name: 'multi-component.md',
    status: 'COMPLETE',
    config:
      '{"path": "/data/media/documents/user-auth0-65363df666d30473af5f30eb/col3544125b631a1337/multi-component.md"}',
    size: 10715,
    created: '2023-12-13T05:56:09.098104+00:00',
    updated: '2023-12-13T05:56:44.326717+00:00',
    sensitive_info: [],
  },
  {
    id: 'docb8b1a6a04b205f3f',
    name: 'parameter-template.md',
    status: 'COMPLETE',
    config:
      '{"path": "/data/media/documents/user-auth0-65363df666d30473af5f30eb/col3544125b631a1337/parameter-template.md"}',
    size: 9797,
    created: '2023-12-13T05:56:09.079208+00:00',
    updated: '2023-12-13T05:56:34.931816+00:00',
    sensitive_info: [],
  },
  {
    id: 'doc457ab5f596874093',
    name: 'environment-variables-and-placeholders.md',
    status: 'COMPLETE',
    config:
      '{"path": "/data/media/documents/user-auth0-65363df666d30473af5f30eb/col3544125b631a1337/environment-variables-and-placeholders.md"}',
    size: 2786,
    created: '2023-12-13T05:56:09.011019+00:00',
    updated: '2023-12-13T05:56:32.475023+00:00',
    sensitive_info: [],
  },
  {
    id: 'docf53916b3f804988e',
    name: 'add-ons-of-kubeblocks.md',
    status: 'COMPLETE',
    config:
      '{"path": "/data/media/documents/user-auth0-65363df666d30473af5f30eb/col3544125b631a1337/add-ons-of-kubeblocks.md"}',
    size: 1539,
    created: '2023-12-13T05:56:09.039840+00:00',
    updated: '2023-12-13T05:56:29.198813+00:00',
    sensitive_info: [],
  },
  {
    id: 'doc94179ec35544ad48',
    name: 'monitoring.md',
    status: 'COMPLETE',
    config:
      '{"path": "/data/media/documents/user-auth0-65363df666d30473af5f30eb/col3544125b631a1337/monitoring.md"}',
    size: 9601,
    created: '2023-12-13T05:56:08.992829+00:00',
    updated: '2023-12-13T05:56:27.376048+00:00',
    sensitive_info: [],
  },
  {
    id: 'doc8a1838a0b5949f84',
    name: 'how-to-add-an-add-on.md',
    status: 'COMPLETE',
    config:
      '{"path": "/data/media/documents/user-auth0-65363df666d30473af5f30eb/col3544125b631a1337/how-to-add-an-add-on.md"}',
    size: 15266,
    created: '2023-12-13T05:56:08.983831+00:00',
    updated: '2023-12-13T05:56:26.741705+00:00',
    sensitive_info: [],
  },
  {
    id: 'doc32630836d74084d8',
    name: 'backup-and-restore.md',
    status: 'COMPLETE',
    config:
      '{"path": "/data/media/documents/user-auth0-65363df666d30473af5f30eb/col3544125b631a1337/backup-and-restore.md"}',
    size: 10406,
    created: '2023-12-13T05:56:08.990158+00:00',
    updated: '2023-12-13T05:56:18.651839+00:00',
    sensitive_info: [],
  },
];

export default {
  'GET /api/v1/collections/:collectionId/documents': {
    code: '200',
    data: documents,
    page_number: 1,
    page_size: 10,
    count: 8,
  },
  'POST /api/v1/collections/:collectionId/documents': {
    code: '200',
  },
  'DELETE /api/v1/collections/:collectionId/documents/:documentId': {
    code: '200',
  },
};
