import _ from 'lodash';

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

const md1 = `
# KubeBlocks overview

## Introduction

KubeBlocks is an open-source, cloud-native data infrastructure designed to help application developers and platform engineers manage database and analytical workloads on Kubernetes. It is cloud-neutral and supports multiple cloud service providers, offering a unified and declarative approach to increase productivity in DevOps practices.


## Key features

- Be compatible with AWS, GCP, Azure, and Alibaba Cloud.
- Supports MySQL, PostgreSQL, Redis, MongoDB, Kafka, and more.
- Provides production-level performance, resilience, scalability, and observability.
- Simplifies day-2 operations, such as upgrading, scaling, monitoring, backup, and restore.
- Contains a powerful and intuitive command line tool.
- Sets up a full-stack, production-ready data infrastructure in minutes.

## Architecture

![KubeBlocks Architecture](https://raw.githubusercontent.com/apecloud/kubeblocks/main/docs/img/kubeblocks-architecture.png)

`;

const md2 =
  '```javascript\nimport React from "react";\nimport { Divider } from "antd";\n```';

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
          collection: collections.find(
            (c) => String(c.id) === req.params.collectionId,
          ),
          history: [
            {
              role: 'human',
              message: `KubeBlocks Introduction`,
            },
            {
              role: 'robot',
              message: md1,
            },
            {
              role: 'human',
              message: `KubeBlocks Introduction`,
            },
            {
              role: 'robot',
              message: md2,
            },
          ],
        },
      ],
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
