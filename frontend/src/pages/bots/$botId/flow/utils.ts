import { NodeData, WorkflowDefinition, WorkflowStyle } from "@/api";
import uniqid from "uniqid";
import Dagre from "@dagrejs/dagre";
import { Position } from "@xyflow/react";
import { ApeEdge, ApeNode, ApeNodeHandlePosition } from "@/types";

const getNodeHandlePositions = (
  direction: WorkflowStyle["layoutDirection"] | undefined = "LR"
): ApeNodeHandlePosition => {
  const positions: ApeNodeHandlePosition = {};
  switch (direction) {
    case "TB":
      Object.assign(positions, {
        sourcePosition: Position.Bottom,
        targetPosition: Position.Top,
      });
      break;
    case "LR":
      Object.assign(positions, {
        sourcePosition: Position.Right,
        targetPosition: Position.Left,
      });
      break;
  }
  return positions;
};

export const getLayoutedElements = (
  nodes: ApeNode[],
  edges: ApeEdge[],
  options: { direction: WorkflowStyle["layoutDirection"] }
): {
  nodes: ApeNode[];
  edges: ApeEdge[];
} => {
  const direction = options.direction;
  const g = new Dagre.graphlib.Graph().setDefaultEdgeLabel(() => ({}));
  g.setGraph({
    rankdir: direction,
    nodesep: 60,
    ranksep: 100,
  });
  edges.forEach((edge) => g.setEdge(edge.source, edge.target));
  nodes.forEach((node) => {
    g.setNode(node.id, {
      ...node,
      width: node.measured?.width ?? 0,
      height: node.measured?.height ?? 0,
    });
  });
  Dagre.layout(g);
  return {
    nodes: nodes.map((node) => {
      const position = g.node(node.id);
      // We are shifting the dagre node position (anchor=center center) to the top left
      // so it matches the React Flow node anchor point (top left).
      const x = position.x - (node.measured?.width ?? 0) / 2;
      const y = position.y - (node.measured?.height ?? 0) / 2;
      return {
        ...node,
        position: { x, y },
        ...getNodeHandlePositions(direction),
      };
    }),
    edges,
  };
};

export const getNodeStartInitData = (): NodeData => ({
  input: {
    schema: {
      type: "object",
      properties: {
        query: {
          type: "string",
          description: "User's question or query",
        },
      },
      required: ["query"],
    },
    values: {
      query: "",
    },
  },
  output: {
    schema: {
      type: "object",
      properties: {
        query: {
          type: "string",
          description: "User's question or query",
        },
      },
      required: ["query"],
    },
  },
});

export const getNodeVectorSearchInitData = (startId: string): NodeData => ({
  input: {
    schema: {
      type: "object",
      properties: {
        top_k: {
          type: "integer",
          default: 5,
          minimum: 1,
          maximum: 10,
          description: "Number of top results to return",
        },
        similarity_threshold: {
          type: "number",
          default: 0.7,
          minimum: 0.1,
          maximum: 1,
          description: "Similarity threshold for vector search",
        },
        query: {
          type: "string",
          description: "User's question or query",
        },
        collection_ids: {
          type: "array",
          items: {
            type: "string",
          },
        },
      },
      required: ["top_k", "similarity_threshold", "query", "collection_ids"],
    },
    values: {
      top_k: 5,
      similarity_threshold: 0.7,
      query: `{{ nodes.${startId}.output.query }}`,
    },
  },
  output: {
    schema: {
      type: "object",
      properties: {
        docs: {
          type: "array",
          description: "Docs from vector search",
          items: {
            $ref: "#/schema/document_with_score",
          },
        },
      },
      required: ["docs"],
    },
  },
});

export const getNodeKeywordSearchInitData = (startId: string): NodeData => ({
  input: {
    schema: {
      type: "object",
      properties: {
        query: {
          type: "string",
          description: "User's question or query",
        },
        top_k: {
          type: "integer",
          default: 3,
          minimum: 1,
          maximum: 10,
          description: "Number of top results to return",
        },
        collection_ids: {
          type: "array",
          items: {
            type: "string",
          },
        },
      },
      required: ["query", "top_k", "collection_ids"],
    },
    values: {
      query: `{{ nodes.${startId}.output.query }}`,
      top_k: 3,
    },
  },
  output: {
    schema: {
      type: "object",
      properties: {
        docs: {
          type: "array",
          description: "Docs from keyword search",
          items: {
            $ref: "#/schema/document_with_score",
          },
        },
      },
      required: ["docs"],
    },
  },
});

export const getNodeMergeNodeInitData = (
  vectorSearchDocsId: string,
  keywordSearchDocsId: string
): NodeData => ({
  input: {
    schema: {
      type: "object",
      properties: {
        merge_strategy: {
          type: "string",
          default: "union",
          enum: ["union", "intersection"],
          description: "How to merge results",
        },
        deduplicate: {
          type: "boolean",
          default: true,
          description: "Whether to deduplicate merged results",
        },
        vector_search_docs: {
          type: "array",
          description: "Docs from vector search",
          items: {
            $ref: "#/schema/document_with_score",
          },
        },
        keyword_search_docs: {
          type: "array",
          description: "Docs from keyword search",
          items: {
            $ref: "#/schema/document_with_score",
          },
        },
      },
      required: [
        "merge_strategy",
        "deduplicate",
        "vector_search_docs",
        "keyword_search_docs",
      ],
    },
    values: {
      merge_strategy: "union",
      deduplicate: true,
      vector_search_docs: `{{ nodes.${vectorSearchDocsId}.output.docs }}`,
      keyword_search_docs: `{{ nodes.${keywordSearchDocsId}.output.docs }}`,
    },
  },
  output: {
    schema: {
      type: "object",
      properties: {
        docs: {
          type: "array",
          description: "Docs after merge",
          items: {
            $ref: "#/schema/document_with_score",
          },
        },
      },
      required: ["docs"],
    },
  },
});

export const getNodeRerankInitData = (mergeId: string): NodeData => ({
  input: {
    schema: {
      type: "object",
      properties: {
        model: {
          type: "string",
          default: "bge-reranker",
          description: "Rerank model name",
        },
        model_service_provider: {
          type: "string",
          default: "openai",
          description: "model service provider",
        },
        docs: {
          type: "array",
          description: "Docs to rerank",
          items: {
            $ref: "#/schema/document_with_score",
          },
        },
      },
      required: ["model", "model_service_provider", "docs"],
    },
    values: {
      model: "bge-reranker",
      model_service_provider: "openai",
      docs: `$\{{ nodes.${mergeId}.output.docs }}`,
    },
  },
  output: {
    schema: {
      type: "object",
      properties: {
        docs: {
          type: "array",
          description: "Docs after rerank",
          items: {
            $ref: "#/schema/document_with_score",
          },
        },
      },
      required: ["docs"],
    },
  },
});

export const getNodeLlmInitData = (
  startId: string,
  rerankId: string
): NodeData => ({
  input: {
    schema: {
      type: "object",
      properties: {
        model_service_provider: {
          type: "string",
          default: "openrouter",
          description: "model service provider",
        },
        model_name: {
          type: "string",
          default: "deepseek/deepseek-v3-base:free",
          description: "model name",
        },
        custom_llm_provider: {
          type: "string",
          default: "openai",
          description: "custom llm provider",
        },
        prompt_template: {
          type: "string",
          default: "{context}\n{query}",
          description: "Prompt template",
        },
        temperature: {
          type: "number",
          default: 0.7,
          minimum: 0,
          maximum: 1,
          description: "Sampling temperature",
        },
        max_tokens: {
          type: "integer",
          default: 1000,
          minimum: 1,
          maximum: 128000,
          description: "Max tokens for generation",
        },
        query: {
          type: "string",
          description: "User's question or query",
        },
        docs: {
          type: "array",
          description: "Docs for LLM context",
          items: {
            $ref: "#/schema/document_with_score",
          },
        },
      },
      required: [
        "model_service_provider",
        "model_name",
        "custom_llm_provider",
        "prompt_template",
        "temperature",
        "max_tokens",
        "query",
        "docs",
      ],
    },
    values: {
      model_service_provider: "openrouter",
      model_name: "deepseek/deepseek-v3-base:free",
      custom_llm_provider: "openrouter",
      prompt_template: "{context}\n{query}",
      temperature: 0.7,
      max_tokens: 1000,
      query: `{{ nodes.${startId}.output.query }}`,
      docs: `{{ nodes.${rerankId}.output.docs }}`,
    },
  },
  output: {
    schema: {
      type: "object",
      properties: {
        text: {
          type: "string",
          description: "text generated by LLM",
        },
      },
    },
  },
});

export const getEdgeId = (): string => uniqid();
export const getInitialData = (): WorkflowDefinition => {
  const startId = uniqid();
  const vectorSearchId = uniqid();
  const keywordSearchId = uniqid();
  const mergeId = uniqid();
  const rerankId = uniqid();
  const llmId = uniqid();

  return {
    name: "rag_flow",
    title: "RAG Knowledge Base Flow",
    description: "A typical RAG flow with parallel retrieval and reranking",
    version: "1.0.0",
    execution: {
      timeout: 300,
      retry: {
        max_attempts: 3,
        delay: 5,
      },
      error_handling: {
        strategy: "stop_on_error",
        notification: {
          email: ["admin@example.com"],
        },
      },
    },
    schema: {
      document_with_score: {
        type: "object",
        properties: {
          doc_id: {
            type: "string",
          },
          text: {
            type: "string",
          },
          score: {
            type: "number",
          },
          metadata: {
            type: "object",
          },
        },
      },
    },
    nodes: [
      {
        id: startId,
        type: "start",
        data: getNodeStartInitData(),
        position: { x: 0, y: 435.5 },
        deletable: false,
        dragHandle: ".drag-handle",
      },
      {
        id: vectorSearchId,
        data: getNodeVectorSearchInitData(startId),
        position: { x: 422, y: 0 },
        type: "vector_search",
        dragHandle: ".drag-handle",
        deletable: false,
      },
      {
        id: keywordSearchId,
        type: "keyword_search",
        data: getNodeKeywordSearchInitData(startId),
        position: { x: 422, y: 610 },
        dragHandle: ".drag-handle",
        deletable: false,
      },
      {
        id: mergeId,
        type: "merge",
        data: getNodeMergeNodeInitData(vectorSearchId, keywordSearchId),
        position: { x: 884, y: 283.5 },
        dragHandle: ".drag-handle",
        deletable: false,
      },
      {
        id: rerankId,
        type: "rerank",
        data: getNodeRerankInitData(mergeId),
        position: { x: 1316, y: 369.5 },
        dragHandle: ".drag-handle",
        deletable: false,
      },
      {
        id: llmId,
        type: "llm",
        data: getNodeLlmInitData(startId, rerankId),
        position: { x: 1718, y: 186.5 },
        dragHandle: ".drag-handle",
        deletable: false,
      },
    ],
    edges: [
      {
        id: getEdgeId(),
        source: startId,
        target: vectorSearchId,
        type: "default",
      },
      {
        id: getEdgeId(),
        source: startId,
        target: keywordSearchId,
        type: "default",
      },
      {
        id: getEdgeId(),
        source: vectorSearchId,
        target: mergeId,
        type: "default",
      },
      {
        id: getEdgeId(),
        source: keywordSearchId,
        target: mergeId,
        type: "default",
      },
      {
        id: getEdgeId(),
        source: mergeId,
        target: rerankId,
        type: "default",
      },
      {
        id: getEdgeId(),
        source: rerankId,
        target: llmId,
        type: "default",
      },
    ],
    style: {
      edgeType: "default",
      layoutDirection: "LR",
    },
  };
};
