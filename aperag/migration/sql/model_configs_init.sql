-- Model configuration initialization SQL script
-- Generated directly from configuration data on 2025-06-12 13:08:58
-- This script populates llm_provider and llm_provider_models tables

BEGIN;

-- Insert/Update LLM Providers

-- Provider: openai
INSERT INTO llm_provider (
    name, label, completion_dialect, embedding_dialect, rerank_dialect, 
    allow_custom_base_url, base_url, gmt_created, gmt_updated
) VALUES (
    'openai', 'OpenAI', 'openai', 'openai', 'jina_ai', 
    FALSE, 'https://api.openai.com/v1', NOW(), NOW()
)
ON CONFLICT (name) DO UPDATE SET
    label = EXCLUDED.label,
    completion_dialect = EXCLUDED.completion_dialect,
    embedding_dialect = EXCLUDED.embedding_dialect,
    rerank_dialect = EXCLUDED.rerank_dialect,
    allow_custom_base_url = EXCLUDED.allow_custom_base_url,
    base_url = EXCLUDED.base_url,
    gmt_updated = NOW();

-- Provider: anthropic
INSERT INTO llm_provider (
    name, label, completion_dialect, embedding_dialect, rerank_dialect, 
    allow_custom_base_url, base_url, gmt_created, gmt_updated
) VALUES (
    'anthropic', 'Anthropic', 'anthropic', 'openai', 'jina_ai', 
    FALSE, 'https://api.anthropic.com', NOW(), NOW()
)
ON CONFLICT (name) DO UPDATE SET
    label = EXCLUDED.label,
    completion_dialect = EXCLUDED.completion_dialect,
    embedding_dialect = EXCLUDED.embedding_dialect,
    rerank_dialect = EXCLUDED.rerank_dialect,
    allow_custom_base_url = EXCLUDED.allow_custom_base_url,
    base_url = EXCLUDED.base_url,
    gmt_updated = NOW();

-- Provider: gemini
INSERT INTO llm_provider (
    name, label, completion_dialect, embedding_dialect, rerank_dialect, 
    allow_custom_base_url, base_url, gmt_created, gmt_updated
) VALUES (
    'gemini', 'Google Gemini', 'google', 'openai', 'jina_ai', 
    FALSE, 'https://generativelanguage.googleapis.com', NOW(), NOW()
)
ON CONFLICT (name) DO UPDATE SET
    label = EXCLUDED.label,
    completion_dialect = EXCLUDED.completion_dialect,
    embedding_dialect = EXCLUDED.embedding_dialect,
    rerank_dialect = EXCLUDED.rerank_dialect,
    allow_custom_base_url = EXCLUDED.allow_custom_base_url,
    base_url = EXCLUDED.base_url,
    gmt_updated = NOW();

-- Provider: xai
INSERT INTO llm_provider (
    name, label, completion_dialect, embedding_dialect, rerank_dialect, 
    allow_custom_base_url, base_url, gmt_created, gmt_updated
) VALUES (
    'xai', 'xAI', 'openai', 'openai', 'jina_ai', 
    FALSE, 'https://api.xai.com/v1', NOW(), NOW()
)
ON CONFLICT (name) DO UPDATE SET
    label = EXCLUDED.label,
    completion_dialect = EXCLUDED.completion_dialect,
    embedding_dialect = EXCLUDED.embedding_dialect,
    rerank_dialect = EXCLUDED.rerank_dialect,
    allow_custom_base_url = EXCLUDED.allow_custom_base_url,
    base_url = EXCLUDED.base_url,
    gmt_updated = NOW();

-- Provider: deepseek
INSERT INTO llm_provider (
    name, label, completion_dialect, embedding_dialect, rerank_dialect, 
    allow_custom_base_url, base_url, gmt_created, gmt_updated
) VALUES (
    'deepseek', 'DeepSeek', 'openai', 'openai', 'jina_ai', 
    FALSE, 'https://api.deepseek.com/v1', NOW(), NOW()
)
ON CONFLICT (name) DO UPDATE SET
    label = EXCLUDED.label,
    completion_dialect = EXCLUDED.completion_dialect,
    embedding_dialect = EXCLUDED.embedding_dialect,
    rerank_dialect = EXCLUDED.rerank_dialect,
    allow_custom_base_url = EXCLUDED.allow_custom_base_url,
    base_url = EXCLUDED.base_url,
    gmt_updated = NOW();

-- Provider: alibabacloud
INSERT INTO llm_provider (
    name, label, completion_dialect, embedding_dialect, rerank_dialect, 
    allow_custom_base_url, base_url, gmt_created, gmt_updated
) VALUES (
    'alibabacloud', 'AlibabaCloud', 'openai', 'openai', 'jina_ai', 
    FALSE, 'https://dashscope.aliyuncs.com/compatible-mode/v1', NOW(), NOW()
)
ON CONFLICT (name) DO UPDATE SET
    label = EXCLUDED.label,
    completion_dialect = EXCLUDED.completion_dialect,
    embedding_dialect = EXCLUDED.embedding_dialect,
    rerank_dialect = EXCLUDED.rerank_dialect,
    allow_custom_base_url = EXCLUDED.allow_custom_base_url,
    base_url = EXCLUDED.base_url,
    gmt_updated = NOW();

-- Provider: siliconflow
INSERT INTO llm_provider (
    name, label, completion_dialect, embedding_dialect, rerank_dialect, 
    allow_custom_base_url, base_url, gmt_created, gmt_updated
) VALUES (
    'siliconflow', 'SiliconFlow', 'openai', 'openai', 'jina_ai', 
    FALSE, 'https://api.siliconflow.cn/v1', NOW(), NOW()
)
ON CONFLICT (name) DO UPDATE SET
    label = EXCLUDED.label,
    completion_dialect = EXCLUDED.completion_dialect,
    embedding_dialect = EXCLUDED.embedding_dialect,
    rerank_dialect = EXCLUDED.rerank_dialect,
    allow_custom_base_url = EXCLUDED.allow_custom_base_url,
    base_url = EXCLUDED.base_url,
    gmt_updated = NOW();

-- Provider: openrouter
INSERT INTO llm_provider (
    name, label, completion_dialect, embedding_dialect, rerank_dialect, 
    allow_custom_base_url, base_url, gmt_created, gmt_updated
) VALUES (
    'openrouter', 'OpenRouter', 'openai', 'openai', 'jina_ai', 
    FALSE, 'https://openrouter.ai/api/v1', NOW(), NOW()
)
ON CONFLICT (name) DO UPDATE SET
    label = EXCLUDED.label,
    completion_dialect = EXCLUDED.completion_dialect,
    embedding_dialect = EXCLUDED.embedding_dialect,
    rerank_dialect = EXCLUDED.rerank_dialect,
    allow_custom_base_url = EXCLUDED.allow_custom_base_url,
    base_url = EXCLUDED.base_url,
    gmt_updated = NOW();

-- Insert/Update Provider Models

-- Completion models for openai
INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openai', 'completion', 'gpt-4', 'openai', 4096, '[]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openai', 'completion', 'gpt-4-turbo', 'openai', 4096, '[]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openai', 'completion', 'gpt-4.1', 'openai', 32768, '[]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openai', 'completion', 'gpt-4.1-mini', 'openai', 32768, '[]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openai', 'completion', 'gpt-4.1-nano', 'openai', 32768, '[]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openai', 'completion', 'gpt-4o', 'openai', 16384, '["recommend"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openai', 'completion', 'gpt-4o-mini', 'openai', 16384, '["recommend"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openai', 'completion', 'o1', 'openai', 100000, '[]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openai', 'completion', 'o1-mini', 'openai', 65536, '[]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openai', 'completion', 'o3', 'openai', 100000, '[]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openai', 'completion', 'o3-mini', 'openai', 100000, '[]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openai', 'completion', 'o4-mini', 'openai', 100000, '[]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

-- Embedding models for openai
INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openai', 'embedding', 'text-embedding-3-large', 'openai', 8191, '[]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openai', 'embedding', 'text-embedding-3-small', 'openai', 8191, '[]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openai', 'embedding', 'text-embedding-ada-002', 'openai', 8191, '[]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openai', 'embedding', 'text-embedding-ada-002-v2', 'openai', 8191, '[]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

-- Completion models for anthropic
INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'anthropic', 'completion', 'claude-3-5-sonnet-latest', 'anthropic', 8192, '["recommend"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'anthropic', 'completion', 'claude-3-7-sonnet-latest', 'anthropic', 128000, '[]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

-- Completion models for gemini
INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'gemini', 'completion', 'gemini/gemini-2.5-flash-preview-04-17', 'gemini', 65535, '["recommend"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'gemini', 'completion', 'gemini/gemini-2.5-pro-preview-03-25', 'gemini', 65535, '["recommend"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

-- Completion models for xai
INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'xai', 'completion', 'xai/grok-3-beta', 'xai', 131072, '[]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'xai', 'completion', 'xai/grok-3-fast-latest', 'xai', 131072, '[]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'xai', 'completion', 'xai/grok-3-mini-beta', 'xai', 131072, '[]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'xai', 'completion', 'xai/grok-3-mini-fast-latest', 'xai', 131072, '[]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

-- Completion models for deepseek
INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'deepseek', 'completion', 'deepseek-r1', 'openai', NULL, '["recommend"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'deepseek', 'completion', 'deepseek-v3', 'openai', NULL, '[]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

-- Completion models for alibabacloud
INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'alibabacloud', 'completion', 'deepseek-r1', 'openai', NULL, '["recommend"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'alibabacloud', 'completion', 'deepseek-v3', 'openai', NULL, '[]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'alibabacloud', 'completion', 'qwen-long', 'openai', NULL, '[]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'alibabacloud', 'completion', 'qwen-max', 'openai', NULL, '["recommend"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'alibabacloud', 'completion', 'qwen-plus', 'openai', NULL, '[]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'alibabacloud', 'completion', 'qwen-plus-latest', 'openai', NULL, '[]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'alibabacloud', 'completion', 'qwen-turbo', 'openai', NULL, '[]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'alibabacloud', 'completion', 'qwen-vl-max', 'openai', NULL, '[]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'alibabacloud', 'completion', 'qwen-vl-plus', 'openai', NULL, '[]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'alibabacloud', 'completion', 'qwq-32b', 'openai', NULL, '[]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'alibabacloud', 'completion', 'qwq-plus', 'openai', NULL, '[]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'alibabacloud', 'completion', 'qwq-plus-latest', 'openai', NULL, '[]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

-- Embedding models for alibabacloud
INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'alibabacloud', 'embedding', 'text-embedding-v1', 'openai', NULL, '[]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'alibabacloud', 'embedding', 'text-embedding-v2', 'openai', NULL, '[]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'alibabacloud', 'embedding', 'text-embedding-v3', 'openai', NULL, '[]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

-- Completion models for siliconflow
INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'siliconflow', 'completion', 'Qwen/QwQ-32B', 'openai', NULL, '[]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'siliconflow', 'completion', 'deepseek-ai/Deepseek-R1', 'openai', NULL, '["recommend"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'siliconflow', 'completion', 'deepseek-ai/Deepseek-V3', 'openai', NULL, '[]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

-- Embedding models for siliconflow
INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'siliconflow', 'embedding', 'BAAI/bge-large-en-v1.5', 'openai', NULL, '[]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'siliconflow', 'embedding', 'BAAI/bge-large-zh-v1.5', 'openai', NULL, '[]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'siliconflow', 'embedding', 'BAAI/bge-m3', 'openai', NULL, '[]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'siliconflow', 'embedding', 'Pro/BAAI/bge-m3', 'openai', NULL, '[]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'siliconflow', 'embedding', 'netease-youdao/bce-embedding-base_v1', 'openai', NULL, '[]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

-- Rerank models for siliconflow
INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'siliconflow', 'rerank', 'BAAI/bge-reranker-v2-m3', 'jina_ai', NULL, '[]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'siliconflow', 'rerank', 'Pro/BAAI/bge-reranker-v2-m3', 'jina_ai', NULL, '[]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'siliconflow', 'rerank', 'netease-youdao/bce-reranker-base_v1', 'jina_ai', NULL, '[]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

-- Completion models for openrouter
INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', '01-ai/yi-large', 'openrouter', 32768, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'aetherwiing/mn-starcannon-12b', 'openrouter', 16384, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'agentica-org/deepcoder-14b-preview:free', 'openrouter', 96000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'ai21/jamba-1.6-large', 'openrouter', 256000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'ai21/jamba-1.6-mini', 'openrouter', 256000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'aion-labs/aion-1.0', 'openrouter', 131072, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'aion-labs/aion-1.0-mini', 'openrouter', 131072, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'aion-labs/aion-rp-llama-3.1-8b', 'openrouter', 32768, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'alfredpros/codellama-7b-instruct-solidity', 'openrouter', 4096, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'all-hands/openhands-lm-32b-v0.1', 'openrouter', 16384, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'alpindale/goliath-120b', 'openrouter', 6144, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'alpindale/magnum-72b', 'openrouter', 16384, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'amazon/nova-lite-v1', 'openrouter', 300000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'amazon/nova-micro-v1', 'openrouter', 128000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'amazon/nova-pro-v1', 'openrouter', 300000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'anthracite-org/magnum-v2-72b', 'openrouter', 32768, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'anthracite-org/magnum-v4-72b', 'openrouter', 16384, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'anthropic/claude-2', 'openrouter', 200000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'anthropic/claude-2.0', 'openrouter', 100000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'anthropic/claude-2.0:beta', 'openrouter', 100000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'anthropic/claude-2.1', 'openrouter', 200000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'anthropic/claude-2.1:beta', 'openrouter', 200000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'anthropic/claude-2:beta', 'openrouter', 200000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'anthropic/claude-3-haiku', 'openrouter', 200000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'anthropic/claude-3-haiku:beta', 'openrouter', 200000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'anthropic/claude-3-opus', 'openrouter', 200000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'anthropic/claude-3-opus:beta', 'openrouter', 200000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'anthropic/claude-3-sonnet', 'openrouter', 200000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'anthropic/claude-3-sonnet:beta', 'openrouter', 200000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'anthropic/claude-3.5-haiku', 'openrouter', 200000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'anthropic/claude-3.5-haiku-20241022', 'openrouter', 200000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'anthropic/claude-3.5-haiku-20241022:beta', 'openrouter', 200000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'anthropic/claude-3.5-haiku:beta', 'openrouter', 200000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'anthropic/claude-3.5-sonnet', 'openrouter', 200000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'anthropic/claude-3.5-sonnet-20240620', 'openrouter', 200000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'anthropic/claude-3.5-sonnet-20240620:beta', 'openrouter', 200000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'anthropic/claude-3.5-sonnet:beta', 'openrouter', 200000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'anthropic/claude-3.7-sonnet', 'openrouter', 200000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'anthropic/claude-3.7-sonnet:beta', 'openrouter', 200000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'anthropic/claude-3.7-sonnet:thinking', 'openrouter', 200000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'anthropic/claude-opus-4', 'openrouter', 200000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'anthropic/claude-sonnet-4', 'openrouter', 200000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'arcee-ai/arcee-blitz', 'openrouter', 32768, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'arcee-ai/caller-large', 'openrouter', 32768, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'arcee-ai/coder-large', 'openrouter', 32768, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'arcee-ai/maestro-reasoning', 'openrouter', 131072, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'arcee-ai/spotlight', 'openrouter', 131072, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'arcee-ai/virtuoso-large', 'openrouter', 131072, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'arcee-ai/virtuoso-medium-v2', 'openrouter', 131072, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'arliai/qwq-32b-arliai-rpr-v1:free', 'openrouter', 32768, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'cognitivecomputations/dolphin-mixtral-8x22b', 'openrouter', 16000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'cognitivecomputations/dolphin3.0-mistral-24b:free', 'openrouter', 32768, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'cognitivecomputations/dolphin3.0-r1-mistral-24b:free', 'openrouter', 32768, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'cohere/command', 'openrouter', 4096, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'cohere/command-a', 'openrouter', 256000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'cohere/command-r', 'openrouter', 128000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'cohere/command-r-03-2024', 'openrouter', 128000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'cohere/command-r-08-2024', 'openrouter', 128000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'cohere/command-r-plus', 'openrouter', 128000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'cohere/command-r-plus-04-2024', 'openrouter', 128000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'cohere/command-r-plus-08-2024', 'openrouter', 128000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'cohere/command-r7b-12-2024', 'openrouter', 128000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'deepseek/deepseek-chat', 'openrouter', 163840, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'deepseek/deepseek-chat-v3-0324', 'openrouter', 163840, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'deepseek/deepseek-chat-v3-0324:free', 'openrouter', 163840, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'deepseek/deepseek-chat:free', 'openrouter', 163840, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'deepseek/deepseek-prover-v2', 'openrouter', 131072, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'deepseek/deepseek-prover-v2:free', 'openrouter', 163840, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'deepseek/deepseek-r1', 'openrouter', 128000, '["free", "recommend"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'deepseek/deepseek-r1-0528', 'openrouter', 128000, '["free", "recommend"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'deepseek/deepseek-r1-0528-qwen3-8b', 'openrouter', 131072, '["free", "recommend"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'deepseek/deepseek-r1-0528-qwen3-8b:free', 'openrouter', 131072, '["free", "recommend"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'deepseek/deepseek-r1-0528:free', 'openrouter', 163840, '["free", "recommend"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'deepseek/deepseek-r1-distill-llama-70b', 'openrouter', 131072, '["free", "recommend"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'deepseek/deepseek-r1-distill-llama-70b:free', 'openrouter', 8192, '["free", "recommend"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'deepseek/deepseek-r1-distill-llama-8b', 'openrouter', 32000, '["free", "recommend"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'deepseek/deepseek-r1-distill-qwen-1.5b', 'openrouter', 131072, '["free", "recommend"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'deepseek/deepseek-r1-distill-qwen-14b', 'openrouter', 64000, '["free", "recommend"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'deepseek/deepseek-r1-distill-qwen-14b:free', 'openrouter', 64000, '["free", "recommend"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'deepseek/deepseek-r1-distill-qwen-32b', 'openrouter', 131072, '["free", "recommend"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'deepseek/deepseek-r1-distill-qwen-32b:free', 'openrouter', 16000, '["free", "recommend"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'deepseek/deepseek-r1-distill-qwen-7b', 'openrouter', 131072, '["free", "recommend"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'deepseek/deepseek-r1-zero:free', 'openrouter', 163840, '["free", "recommend"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'deepseek/deepseek-r1:free', 'openrouter', 163840, '["free", "recommend"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'deepseek/deepseek-v3-base:free', 'openrouter', 163840, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'eleutherai/llemma_7b', 'openrouter', 4096, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'eva-unit-01/eva-llama-3.33-70b', 'openrouter', 16384, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'eva-unit-01/eva-qwen-2.5-32b', 'openrouter', 16384, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'eva-unit-01/eva-qwen-2.5-72b', 'openrouter', 16384, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'featherless/qwerky-72b:free', 'openrouter', 32768, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'google/gemini-2.0-flash-001', 'openrouter', 1048576, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'google/gemini-2.0-flash-exp:free', 'openrouter', 1048576, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'google/gemini-2.0-flash-lite-001', 'openrouter', 1048576, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'google/gemini-2.5-flash-preview', 'openrouter', 1048576, '["free", "recommend"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'google/gemini-2.5-flash-preview-05-20', 'openrouter', 1048576, '["free", "recommend"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'google/gemini-2.5-flash-preview-05-20:thinking', 'openrouter', 1048576, '["free", "recommend"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'google/gemini-2.5-flash-preview:thinking', 'openrouter', 1048576, '["free", "recommend"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'google/gemini-2.5-pro-exp-03-25', 'openrouter', 1048576, '["free", "recommend"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'google/gemini-2.5-pro-preview', 'openrouter', 1048576, '["free", "recommend"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'google/gemini-2.5-pro-preview-05-06', 'openrouter', 1048576, '["free", "recommend"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'google/gemini-flash-1.5', 'openrouter', 1000000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'google/gemini-flash-1.5-8b', 'openrouter', 1000000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'google/gemini-pro-1.5', 'openrouter', 2000000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'google/gemma-2-27b-it', 'openrouter', 8192, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'google/gemma-2-9b-it', 'openrouter', 8192, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'google/gemma-2-9b-it:free', 'openrouter', 8192, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'google/gemma-3-12b-it', 'openrouter', 131072, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'google/gemma-3-12b-it:free', 'openrouter', 96000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'google/gemma-3-1b-it:free', 'openrouter', 32768, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'google/gemma-3-27b-it', 'openrouter', 131072, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'google/gemma-3-27b-it:free', 'openrouter', 96000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'google/gemma-3-4b-it', 'openrouter', 131072, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'google/gemma-3-4b-it:free', 'openrouter', 96000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'google/gemma-3n-e4b-it:free', 'openrouter', 8192, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'gryphe/mythomax-l2-13b', 'openrouter', 4096, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'inception/mercury-coder-small-beta', 'openrouter', 32000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'infermatic/mn-inferor-12b', 'openrouter', 16384, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'inflection/inflection-3-pi', 'openrouter', 8000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'inflection/inflection-3-productivity', 'openrouter', 8000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'liquid/lfm-3b', 'openrouter', 32768, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'liquid/lfm-40b', 'openrouter', 32768, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'liquid/lfm-7b', 'openrouter', 32768, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'mancer/weaver', 'openrouter', 8000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'meta-llama/llama-2-70b-chat', 'openrouter', 4096, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'meta-llama/llama-3-70b-instruct', 'openrouter', 8192, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'meta-llama/llama-3-8b-instruct', 'openrouter', 8192, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'meta-llama/llama-3.1-405b', 'openrouter', 32768, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'meta-llama/llama-3.1-405b-instruct', 'openrouter', 32768, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'meta-llama/llama-3.1-405b:free', 'openrouter', 64000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'meta-llama/llama-3.1-70b-instruct', 'openrouter', 131072, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'meta-llama/llama-3.1-8b-instruct', 'openrouter', 131000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'meta-llama/llama-3.1-8b-instruct:free', 'openrouter', 131072, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'meta-llama/llama-3.2-11b-vision-instruct', 'openrouter', 131072, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'meta-llama/llama-3.2-11b-vision-instruct:free', 'openrouter', 131072, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'meta-llama/llama-3.2-1b-instruct', 'openrouter', 131072, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'meta-llama/llama-3.2-1b-instruct:free', 'openrouter', 131072, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'meta-llama/llama-3.2-3b-instruct', 'openrouter', 131072, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'meta-llama/llama-3.2-3b-instruct:free', 'openrouter', 20000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'meta-llama/llama-3.2-90b-vision-instruct', 'openrouter', 131072, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'meta-llama/llama-3.3-70b-instruct', 'openrouter', 131072, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'meta-llama/llama-3.3-70b-instruct:free', 'openrouter', 131072, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'meta-llama/llama-3.3-8b-instruct:free', 'openrouter', 128000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'meta-llama/llama-4-maverick', 'openrouter', 1048576, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'meta-llama/llama-4-maverick:free', 'openrouter', 128000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'meta-llama/llama-4-scout', 'openrouter', 1048576, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'meta-llama/llama-4-scout:free', 'openrouter', 200000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'meta-llama/llama-guard-2-8b', 'openrouter', 8192, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'meta-llama/llama-guard-3-8b', 'openrouter', 131072, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'meta-llama/llama-guard-4-12b', 'openrouter', 163840, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'microsoft/mai-ds-r1:free', 'openrouter', 163840, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'microsoft/phi-3-medium-128k-instruct', 'openrouter', 128000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'microsoft/phi-3-mini-128k-instruct', 'openrouter', 128000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'microsoft/phi-3.5-mini-128k-instruct', 'openrouter', 128000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'microsoft/phi-4', 'openrouter', 16384, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'microsoft/phi-4-multimodal-instruct', 'openrouter', 131072, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'microsoft/phi-4-reasoning-plus', 'openrouter', 32768, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'microsoft/phi-4-reasoning-plus:free', 'openrouter', 32768, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'microsoft/phi-4-reasoning:free', 'openrouter', 32768, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'microsoft/wizardlm-2-8x22b', 'openrouter', 65536, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'minimax/minimax-01', 'openrouter', 1000192, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'mistralai/codestral-2501', 'openrouter', 262144, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'mistralai/devstral-small', 'openrouter', 128000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'mistralai/devstral-small:free', 'openrouter', 131072, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'mistralai/magistral-medium-2506', 'openrouter', 40960, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'mistralai/magistral-medium-2506:thinking', 'openrouter', 40960, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'mistralai/magistral-small-2506', 'openrouter', 40000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'mistralai/ministral-3b', 'openrouter', 131072, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'mistralai/ministral-8b', 'openrouter', 128000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'mistralai/mistral-7b-instruct', 'openrouter', 32768, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'mistralai/mistral-7b-instruct-v0.1', 'openrouter', 2824, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'mistralai/mistral-7b-instruct-v0.2', 'openrouter', 32768, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'mistralai/mistral-7b-instruct-v0.3', 'openrouter', 32768, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'mistralai/mistral-7b-instruct:free', 'openrouter', 32768, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'mistralai/mistral-large', 'openrouter', 128000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'mistralai/mistral-large-2407', 'openrouter', 131072, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'mistralai/mistral-large-2411', 'openrouter', 131072, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'mistralai/mistral-medium', 'openrouter', 32768, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'mistralai/mistral-medium-3', 'openrouter', 32768, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'mistralai/mistral-nemo', 'openrouter', 131072, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'mistralai/mistral-nemo:free', 'openrouter', 131072, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'mistralai/mistral-saba', 'openrouter', 32768, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'mistralai/mistral-small', 'openrouter', 32768, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'mistralai/mistral-small-24b-instruct-2501', 'openrouter', 32768, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'mistralai/mistral-small-24b-instruct-2501:free', 'openrouter', 32768, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'mistralai/mistral-small-3.1-24b-instruct', 'openrouter', 131072, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'mistralai/mistral-small-3.1-24b-instruct:free', 'openrouter', 96000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'mistralai/mistral-tiny', 'openrouter', 32768, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'mistralai/mixtral-8x22b-instruct', 'openrouter', 65536, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'mistralai/mixtral-8x7b-instruct', 'openrouter', 32768, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'mistralai/pixtral-12b', 'openrouter', 32768, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'mistralai/pixtral-large-2411', 'openrouter', 131072, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'moonshotai/kimi-vl-a3b-thinking:free', 'openrouter', 131072, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'moonshotai/moonlight-16b-a3b-instruct:free', 'openrouter', 8192, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'neversleep/llama-3-lumimaid-70b', 'openrouter', 8192, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'neversleep/llama-3-lumimaid-8b', 'openrouter', 24576, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'neversleep/llama-3.1-lumimaid-70b', 'openrouter', 16384, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'neversleep/llama-3.1-lumimaid-8b', 'openrouter', 32768, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'neversleep/noromaid-20b', 'openrouter', 8192, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'nothingiisreal/mn-celeste-12b', 'openrouter', 16384, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'nousresearch/deephermes-3-llama-3-8b-preview:free', 'openrouter', 131072, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'nousresearch/deephermes-3-mistral-24b-preview:free', 'openrouter', 32768, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'nousresearch/hermes-2-pro-llama-3-8b', 'openrouter', 131072, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'nousresearch/hermes-3-llama-3.1-405b', 'openrouter', 131072, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'nousresearch/hermes-3-llama-3.1-70b', 'openrouter', 131072, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'nousresearch/nous-hermes-2-mixtral-8x7b-dpo', 'openrouter', 32768, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'nvidia/llama-3.1-nemotron-70b-instruct', 'openrouter', 131072, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'nvidia/llama-3.1-nemotron-ultra-253b-v1', 'openrouter', 131072, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'nvidia/llama-3.1-nemotron-ultra-253b-v1:free', 'openrouter', 131072, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'nvidia/llama-3.3-nemotron-super-49b-v1', 'openrouter', 131072, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'nvidia/llama-3.3-nemotron-super-49b-v1:free', 'openrouter', 131072, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'open-r1/olympiccoder-32b:free', 'openrouter', 32768, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'openai/chatgpt-4o-latest', 'openrouter', 128000, '["free", "recommend"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'openai/codex-mini', 'openrouter', 200000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'openai/gpt-3.5-turbo', 'openrouter', 16385, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'openai/gpt-3.5-turbo-0125', 'openrouter', 16385, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'openai/gpt-3.5-turbo-0613', 'openrouter', 4095, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'openai/gpt-3.5-turbo-1106', 'openrouter', 16385, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'openai/gpt-3.5-turbo-16k', 'openrouter', 16385, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'openai/gpt-3.5-turbo-instruct', 'openrouter', 4095, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'openai/gpt-4', 'openrouter', 8191, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'openai/gpt-4-0314', 'openrouter', 8191, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'openai/gpt-4-1106-preview', 'openrouter', 128000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'openai/gpt-4-turbo', 'openrouter', 128000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'openai/gpt-4-turbo-preview', 'openrouter', 128000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'openai/gpt-4.1', 'openrouter', 1047576, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'openai/gpt-4.1-mini', 'openrouter', 1047576, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'openai/gpt-4.1-nano', 'openrouter', 1047576, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'openai/gpt-4.5-preview', 'openrouter', 128000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'openai/gpt-4o', 'openrouter', 128000, '["free", "recommend"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'openai/gpt-4o-2024-05-13', 'openrouter', 128000, '["free", "recommend"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'openai/gpt-4o-2024-08-06', 'openrouter', 128000, '["free", "recommend"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'openai/gpt-4o-2024-11-20', 'openrouter', 128000, '["free", "recommend"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'openai/gpt-4o-mini', 'openrouter', 128000, '["free", "recommend"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'openai/gpt-4o-mini-2024-07-18', 'openrouter', 128000, '["free", "recommend"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'openai/gpt-4o-mini-search-preview', 'openrouter', 128000, '["free", "recommend"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'openai/gpt-4o-search-preview', 'openrouter', 128000, '["free", "recommend"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'openai/gpt-4o:extended', 'openrouter', 128000, '["free", "recommend"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'openai/o1', 'openrouter', 200000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'openai/o1-mini', 'openrouter', 128000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'openai/o1-mini-2024-09-12', 'openrouter', 128000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'openai/o1-preview', 'openrouter', 128000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'openai/o1-preview-2024-09-12', 'openrouter', 128000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'openai/o1-pro', 'openrouter', 200000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'openai/o3', 'openrouter', 200000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'openai/o3-mini', 'openrouter', 200000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'openai/o3-mini-high', 'openrouter', 200000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'openai/o3-pro', 'openrouter', 200000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'openai/o4-mini', 'openrouter', 200000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'openai/o4-mini-high', 'openrouter', 200000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'opengvlab/internvl3-14b:free', 'openrouter', 32000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'opengvlab/internvl3-2b:free', 'openrouter', 32000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'openrouter/auto', 'openrouter', 2000000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'perplexity/llama-3.1-sonar-large-128k-online', 'openrouter', 127072, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'perplexity/llama-3.1-sonar-small-128k-online', 'openrouter', 127072, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'perplexity/r1-1776', 'openrouter', 128000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'perplexity/sonar', 'openrouter', 127072, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'perplexity/sonar-deep-research', 'openrouter', 128000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'perplexity/sonar-pro', 'openrouter', 200000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'perplexity/sonar-reasoning', 'openrouter', 127000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'perplexity/sonar-reasoning-pro', 'openrouter', 128000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'pygmalionai/mythalion-13b', 'openrouter', 4096, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'qwen/qwen-2-72b-instruct', 'openrouter', 32768, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'qwen/qwen-2.5-72b-instruct', 'openrouter', 32768, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'qwen/qwen-2.5-72b-instruct:free', 'openrouter', 32768, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'qwen/qwen-2.5-7b-instruct', 'openrouter', 32768, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'qwen/qwen-2.5-7b-instruct:free', 'openrouter', 32768, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'qwen/qwen-2.5-coder-32b-instruct', 'openrouter', 32768, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'qwen/qwen-2.5-coder-32b-instruct:free', 'openrouter', 32768, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'qwen/qwen-2.5-vl-7b-instruct', 'openrouter', 32768, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'qwen/qwen-2.5-vl-7b-instruct:free', 'openrouter', 32768, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'qwen/qwen-max', 'openrouter', 32768, '["free", "recommend"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'qwen/qwen-plus', 'openrouter', 131072, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'qwen/qwen-turbo', 'openrouter', 1000000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'qwen/qwen-vl-max', 'openrouter', 7500, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'qwen/qwen-vl-plus', 'openrouter', 7500, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'qwen/qwen2.5-vl-32b-instruct', 'openrouter', 128000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'qwen/qwen2.5-vl-32b-instruct:free', 'openrouter', 8192, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'qwen/qwen2.5-vl-3b-instruct:free', 'openrouter', 64000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'qwen/qwen2.5-vl-72b-instruct', 'openrouter', 32000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'qwen/qwen2.5-vl-72b-instruct:free', 'openrouter', 131072, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'qwen/qwen3-14b', 'openrouter', 40960, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'qwen/qwen3-14b:free', 'openrouter', 40960, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'qwen/qwen3-235b-a22b', 'openrouter', 40960, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'qwen/qwen3-235b-a22b:free', 'openrouter', 40960, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'qwen/qwen3-30b-a3b', 'openrouter', 40960, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'qwen/qwen3-30b-a3b:free', 'openrouter', 40960, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'qwen/qwen3-32b', 'openrouter', 40960, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'qwen/qwen3-32b:free', 'openrouter', 40960, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'qwen/qwen3-8b', 'openrouter', 128000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'qwen/qwen3-8b:free', 'openrouter', 40960, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'qwen/qwq-32b', 'openrouter', 131072, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'qwen/qwq-32b-preview', 'openrouter', 32768, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'qwen/qwq-32b:free', 'openrouter', 40000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'raifle/sorcererlm-8x22b', 'openrouter', 16000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'rekaai/reka-flash-3:free', 'openrouter', 32768, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'sao10k/fimbulvetr-11b-v2', 'openrouter', 4096, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'sao10k/l3-euryale-70b', 'openrouter', 8192, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'sao10k/l3-lunaris-8b', 'openrouter', 8192, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'sao10k/l3.1-euryale-70b', 'openrouter', 131072, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'sao10k/l3.3-euryale-70b', 'openrouter', 131072, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'sarvamai/sarvam-m:free', 'openrouter', 32768, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'scb10x/llama3.1-typhoon2-70b-instruct', 'openrouter', 8192, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'sentientagi/dobby-mini-unhinged-plus-llama-3.1-8b', 'openrouter', 131072, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'shisa-ai/shisa-v2-llama3.3-70b:free', 'openrouter', 32768, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'sophosympatheia/midnight-rose-70b', 'openrouter', 4096, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'thedrummer/anubis-pro-105b-v1', 'openrouter', 131072, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'thedrummer/rocinante-12b', 'openrouter', 32768, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'thedrummer/skyfall-36b-v2', 'openrouter', 32768, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'thedrummer/unslopnemo-12b', 'openrouter', 32000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'thedrummer/valkyrie-49b-v1', 'openrouter', 131072, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'thudm/glm-4-32b', 'openrouter', 32000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'thudm/glm-4-32b:free', 'openrouter', 32768, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'thudm/glm-z1-32b', 'openrouter', 32000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'thudm/glm-z1-32b:free', 'openrouter', 32768, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'thudm/glm-z1-rumination-32b', 'openrouter', 32000, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'tngtech/deepseek-r1t-chimera:free', 'openrouter', 163840, '["free", "recommend"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'undi95/remm-slerp-l2-13b', 'openrouter', 4096, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'undi95/toppy-m-7b', 'openrouter', 4096, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'x-ai/grok-2-1212', 'openrouter', 131072, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'x-ai/grok-2-vision-1212', 'openrouter', 32768, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'x-ai/grok-3-beta', 'openrouter', 131072, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'x-ai/grok-3-mini-beta', 'openrouter', 131072, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'x-ai/grok-beta', 'openrouter', 131072, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

INSERT INTO llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    'openrouter', 'completion', 'x-ai/grok-vision-beta', 'openrouter', 8192, '["free"]'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();

COMMIT;

-- Script completed. Generated on 2025-06-12 13:08:58
-- Total providers: 8
-- Total models: 376