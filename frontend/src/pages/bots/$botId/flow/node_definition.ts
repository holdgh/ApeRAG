import { NodeData } from "@/api";

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
      top_k: 5,
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
