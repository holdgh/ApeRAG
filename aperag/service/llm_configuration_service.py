# Copyright 2025 ApeCloud, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from http import HTTPStatus
from typing import Optional

from django.utils import timezone

from aperag.db import models as db_models
from aperag.views.utils import fail, success


async def get_llm_configuration():
    """Get complete LLM configuration including providers and models"""
    try:
        # Get all providers
        providers_query = db_models.LLMProvider.objects.filter(gmt_deleted__isnull=True)
        providers_data = []

        async for provider in providers_query:
            providers_data.append(
                {
                    "name": provider.name,
                    "label": provider.label,
                    "completion_dialect": provider.completion_dialect,
                    "embedding_dialect": provider.embedding_dialect,
                    "rerank_dialect": provider.rerank_dialect,
                    "allow_custom_base_url": provider.allow_custom_base_url,
                    "base_url": provider.base_url,
                    "extra": provider.extra,
                    "created": provider.gmt_created,
                    "updated": provider.gmt_updated,
                }
            )

        # Get all models
        models_query = db_models.LLMProviderModel.objects.filter(gmt_deleted__isnull=True)
        models_data = []

        async for model in models_query:
            models_data.append(
                {
                    "provider_name": model.provider_name,
                    "api": model.api,
                    "model": model.model,
                    "custom_llm_provider": model.custom_llm_provider,
                    "max_tokens": model.max_tokens,
                    "tags": model.tags or [],
                    "created": model.gmt_created,
                    "updated": model.gmt_updated,
                }
            )

        return success(
            {
                "providers": providers_data,
                "models": models_data,
            }
        )
    except Exception as e:
        return fail(HTTPStatus.INTERNAL_SERVER_ERROR, f"Failed to get LLM configuration: {str(e)}")


async def list_llm_providers():
    """List all LLM providers"""
    try:
        query = db_models.LLMProvider.objects.filter(gmt_deleted__isnull=True)
        providers_data = []

        async for provider in query:
            providers_data.append(
                {
                    "name": provider.name,
                    "label": provider.label,
                    "completion_dialect": provider.completion_dialect,
                    "embedding_dialect": provider.embedding_dialect,
                    "rerank_dialect": provider.rerank_dialect,
                    "allow_custom_base_url": provider.allow_custom_base_url,
                    "base_url": provider.base_url,
                    "extra": provider.extra,
                    "created": provider.gmt_created,
                    "updated": provider.gmt_updated,
                }
            )

        return success(
            {
                "items": providers_data,
                "pageResult": {
                    "page_number": 1,
                    "page_size": len(providers_data),
                    "count": len(providers_data),
                },
            }
        )
    except Exception as e:
        return fail(HTTPStatus.INTERNAL_SERVER_ERROR, f"Failed to list LLM providers: {str(e)}")


async def create_llm_provider(provider_data: dict):
    """Create a new LLM provider"""
    try:
        # Check if provider with same name already exists
        existing = await db_models.LLMProvider.objects.filter(
            name=provider_data["name"], gmt_deleted__isnull=True
        ).afirst()

        if existing:
            return fail(HTTPStatus.BAD_REQUEST, f"Provider with name '{provider_data['name']}' already exists")

        # Create new provider
        provider = await db_models.LLMProvider.objects.acreate(
            name=provider_data["name"],
            label=provider_data["label"],
            completion_dialect=provider_data.get("completion_dialect", "openai"),
            embedding_dialect=provider_data.get("embedding_dialect", "openai"),
            rerank_dialect=provider_data.get("rerank_dialect", "jina_ai"),
            allow_custom_base_url=provider_data.get("allow_custom_base_url", False),
            base_url=provider_data["base_url"],
            extra=provider_data.get("extra"),
        )

        return success(
            {
                "name": provider.name,
                "label": provider.label,
                "completion_dialect": provider.completion_dialect,
                "embedding_dialect": provider.embedding_dialect,
                "rerank_dialect": provider.rerank_dialect,
                "allow_custom_base_url": provider.allow_custom_base_url,
                "base_url": provider.base_url,
                "extra": provider.extra,
                "created": provider.gmt_created,
                "updated": provider.gmt_updated,
            }
        )
    except Exception as e:
        return fail(HTTPStatus.INTERNAL_SERVER_ERROR, f"Failed to create LLM provider: {str(e)}")


async def get_llm_provider(provider_name: str):
    """Get a specific LLM provider by name"""
    try:
        provider = await db_models.LLMProvider.objects.filter(name=provider_name, gmt_deleted__isnull=True).afirst()

        if not provider:
            return fail(HTTPStatus.NOT_FOUND, f"Provider '{provider_name}' not found")

        return success(
            {
                "name": provider.name,
                "label": provider.label,
                "completion_dialect": provider.completion_dialect,
                "embedding_dialect": provider.embedding_dialect,
                "rerank_dialect": provider.rerank_dialect,
                "allow_custom_base_url": provider.allow_custom_base_url,
                "base_url": provider.base_url,
                "extra": provider.extra,
                "created": provider.gmt_created,
                "updated": provider.gmt_updated,
            }
        )
    except Exception as e:
        return fail(HTTPStatus.INTERNAL_SERVER_ERROR, f"Failed to get LLM provider: {str(e)}")


async def update_llm_provider(provider_name: str, update_data: dict):
    """Update an existing LLM provider"""
    try:
        provider = await db_models.LLMProvider.objects.filter(name=provider_name, gmt_deleted__isnull=True).afirst()

        if not provider:
            return fail(HTTPStatus.NOT_FOUND, f"Provider '{provider_name}' not found")

        # Update fields
        for field, value in update_data.items():
            if value is not None and hasattr(provider, field):
                setattr(provider, field, value)

        provider.gmt_updated = timezone.now()
        await provider.asave()

        return success(
            {
                "name": provider.name,
                "label": provider.label,
                "completion_dialect": provider.completion_dialect,
                "embedding_dialect": provider.embedding_dialect,
                "rerank_dialect": provider.rerank_dialect,
                "allow_custom_base_url": provider.allow_custom_base_url,
                "base_url": provider.base_url,
                "extra": provider.extra,
                "created": provider.gmt_created,
                "updated": provider.gmt_updated,
            }
        )
    except Exception as e:
        return fail(HTTPStatus.INTERNAL_SERVER_ERROR, f"Failed to update LLM provider: {str(e)}")


async def delete_llm_provider(provider_name: str):
    """Delete an LLM provider (soft delete)"""
    try:
        provider = await db_models.LLMProvider.objects.filter(name=provider_name, gmt_deleted__isnull=True).afirst()

        if not provider:
            return fail(HTTPStatus.NOT_FOUND, f"Provider '{provider_name}' not found")

        # Soft delete the provider
        provider.gmt_deleted = timezone.now()
        provider.gmt_updated = timezone.now()
        await provider.asave()

        # Also soft delete all models for this provider
        await db_models.LLMProviderModel.objects.filter(provider_name=provider_name, gmt_deleted__isnull=True).aupdate(
            gmt_deleted=timezone.now(), gmt_updated=timezone.now()
        )

        return success(None)
    except Exception as e:
        return fail(HTTPStatus.INTERNAL_SERVER_ERROR, f"Failed to delete LLM provider: {str(e)}")


async def list_llm_provider_models(provider_name: Optional[str] = None):
    """List LLM provider models, optionally filtered by provider"""
    try:
        query = db_models.LLMProviderModel.objects.filter(gmt_deleted__isnull=True)

        if provider_name:
            query = query.filter(provider_name=provider_name)

        models_data = []
        async for model in query:
            models_data.append(
                {
                    "provider_name": model.provider_name,
                    "api": model.api,
                    "model": model.model,
                    "custom_llm_provider": model.custom_llm_provider,
                    "max_tokens": model.max_tokens,
                    "tags": model.tags or [],
                    "created": model.gmt_created,
                    "updated": model.gmt_updated,
                }
            )

        return success(
            {
                "items": models_data,
                "pageResult": {
                    "page_number": 1,
                    "page_size": len(models_data),
                    "count": len(models_data),
                },
            }
        )
    except Exception as e:
        return fail(HTTPStatus.INTERNAL_SERVER_ERROR, f"Failed to list LLM provider models: {str(e)}")


async def create_llm_provider_model(provider_name: str, model_data: dict):
    """Create a new model for a specific provider"""
    try:
        # Check if provider exists
        provider = await db_models.LLMProvider.objects.filter(name=provider_name, gmt_deleted__isnull=True).afirst()

        if not provider:
            return fail(HTTPStatus.NOT_FOUND, f"Provider '{provider_name}' not found")

        # Check if model already exists
        existing = await db_models.LLMProviderModel.objects.filter(
            provider_name=provider_name, api=model_data["api"], model=model_data["model"], gmt_deleted__isnull=True
        ).afirst()

        if existing:
            return fail(
                HTTPStatus.BAD_REQUEST,
                f"Model '{model_data['model']}' for API '{model_data['api']}' already exists for provider '{provider_name}'",
            )

        # Create new model
        model = await db_models.LLMProviderModel.objects.acreate(
            provider_name=provider_name,
            api=model_data["api"],
            model=model_data["model"],
            custom_llm_provider=model_data["custom_llm_provider"],
            max_tokens=model_data.get("max_tokens"),
            tags=model_data.get("tags", []),
        )

        return success(
            {
                "provider_name": model.provider_name,
                "api": model.api,
                "model": model.model,
                "custom_llm_provider": model.custom_llm_provider,
                "max_tokens": model.max_tokens,
                "tags": model.tags or [],
                "created": model.gmt_created,
                "updated": model.gmt_updated,
            }
        )
    except Exception as e:
        return fail(HTTPStatus.INTERNAL_SERVER_ERROR, f"Failed to create LLM provider model: {str(e)}")


async def update_llm_provider_model(provider_name: str, api: str, model: str, update_data: dict):
    """Update a specific model of a provider"""
    try:
        model_obj = await db_models.LLMProviderModel.objects.filter(
            provider_name=provider_name, api=api, model=model, gmt_deleted__isnull=True
        ).afirst()

        if not model_obj:
            return fail(
                HTTPStatus.NOT_FOUND, f"Model '{model}' for API '{api}' not found for provider '{provider_name}'"
            )

        # Update fields
        for field, value in update_data.items():
            if value is not None and hasattr(model_obj, field):
                setattr(model_obj, field, value)

        model_obj.gmt_updated = timezone.now()
        await model_obj.asave()

        return success(
            {
                "provider_name": model_obj.provider_name,
                "api": model_obj.api,
                "model": model_obj.model,
                "custom_llm_provider": model_obj.custom_llm_provider,
                "max_tokens": model_obj.max_tokens,
                "tags": model_obj.tags or [],
                "created": model_obj.gmt_created,
                "updated": model_obj.gmt_updated,
            }
        )
    except Exception as e:
        return fail(HTTPStatus.INTERNAL_SERVER_ERROR, f"Failed to update LLM provider model: {str(e)}")


async def delete_llm_provider_model(provider_name: str, api: str, model: str):
    """Delete a specific model of a provider"""
    try:
        model_obj = await db_models.LLMProviderModel.objects.filter(
            provider_name=provider_name, api=api, model=model, gmt_deleted__isnull=True
        ).afirst()

        if not model_obj:
            return fail(
                HTTPStatus.NOT_FOUND, f"Model '{model}' for API '{api}' not found for provider '{provider_name}'"
            )

        # Soft delete the model
        model_obj.gmt_deleted = timezone.now()
        model_obj.gmt_updated = timezone.now()
        await model_obj.asave()

        return success(None)
    except Exception as e:
        return fail(HTTPStatus.INTERNAL_SERVER_ERROR, f"Failed to delete LLM provider model: {str(e)}")
