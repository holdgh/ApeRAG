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
from typing import List

from django.utils import timezone

from aperag.db import models as db_models
from aperag.db.ops import query_msp, query_msp_list
from aperag.schema import view_models
from aperag.schema.view_models import ModelServiceProvider, ModelServiceProviderList
from aperag.service.llm_config_service import get_model_config_objects, get_model_configs, get_supported_provider_names
from aperag.views.utils import fail, success


async def build_model_service_provider_response(
    msp: db_models.ModelServiceProvider, supported_msp: view_models.ModelServiceProvider
) -> view_models.ModelServiceProvider:
    """Build ModelServiceProvider response object for API return."""
    # Get LLMProvider data for dialect and base_url information
    llm_provider = await db_models.LLMProvider.objects.aget(name=msp.name)
    base_url = llm_provider.base_url
    completion_dialect = llm_provider.completion_dialect
    embedding_dialect = llm_provider.embedding_dialect
    rerank_dialect = llm_provider.rerank_dialect

    return view_models.ModelServiceProvider(
        name=msp.name,
        completion_dialect=completion_dialect,
        embedding_dialect=embedding_dialect,
        rerank_dialect=rerank_dialect,
        label=supported_msp.label,
        allow_custom_base_url=supported_msp.allow_custom_base_url,
        base_url=base_url,
        api_key=msp.api_key,
    )


async def list_model_service_providers(user: str) -> view_models.ModelServiceProviderList:
    model_configs = await get_model_configs()
    supported_msp_dict = {msp["name"]: ModelServiceProvider(**msp) for msp in model_configs}
    msp_list = await query_msp_list(user)
    response = []
    for msp in msp_list:
        if msp.name in supported_msp_dict:
            supported_msp = supported_msp_dict[msp.name]
            response.append(await build_model_service_provider_response(msp, supported_msp))
    return success(ModelServiceProviderList(items=response))


async def update_model_service_provider(
    user: str,
    provider: str,
    mspIn: view_models.ModelServiceProviderUpdate,
    supported_providers: List[view_models.ModelServiceProvider],
):
    supported_msp_names = {provider.name for provider in supported_providers if provider.name}
    if provider not in supported_msp_names:
        return fail(HTTPStatus.BAD_REQUEST, f"unsupported model service provider {provider}")
    msp_config = next(item for item in supported_providers if item.name == provider)
    if not msp_config.allow_custom_base_url and mspIn.base_url is not None:
        return fail(HTTPStatus.BAD_REQUEST, f"model service provider {provider} does not support setting base_url")

    # For now, base_url and extra are stored in LLMProvider, but this update endpoint only handles api_key for ModelServiceProvider
    # The mspIn.base_url and mspIn.extra should be handled by LLMProvider management if needed

    msp = await query_msp(user, provider, filterDeletion=False)
    if msp is None:
        msp = db_models.ModelServiceProvider(
            user=user,
            name=provider,
            api_key=mspIn.api_key,
            status=db_models.ModelServiceProvider.Status.ACTIVE,
        )
    else:
        if msp.status == db_models.ModelServiceProvider.Status.DELETED:
            msp.status = db_models.ModelServiceProvider.Status.ACTIVE
            msp.gmt_deleted = None
        msp.api_key = mspIn.api_key
    await msp.asave()
    return success({})


async def delete_model_service_provider(user: str, provider: str):
    supported_msp_names = await get_supported_provider_names()
    if provider not in supported_msp_names:
        return fail(HTTPStatus.BAD_REQUEST, f"unsupported model service provider {provider}")
    msp = await query_msp(user, provider)
    if msp is None:
        return fail(HTTPStatus.NOT_FOUND, f"model service provider {provider} not found")
    msp.status = db_models.ModelServiceProvider.Status.DELETED
    msp.gmt_deleted = timezone.now()
    await msp.asave()
    return success({})


async def list_available_models(user: str) -> view_models.ModelConfigList:
    from aperag.schema.view_models import ModelConfigList

    supported_providers = await get_model_config_objects()
    supported_msp_dict = {provider.name: provider for provider in supported_providers}
    msp_list = await query_msp_list(user)
    available_providers = []
    for msp in msp_list:
        if msp.name in supported_msp_dict:
            available_providers.append(supported_msp_dict[msp.name])
    return success(ModelConfigList(items=available_providers, pageResult=None).model_dump(exclude_none=True))


async def list_supported_model_service_providers() -> view_models.ModelServiceProviderList:
    model_configs = await get_model_configs()
    response = []
    for supported_msp in model_configs:
        provider = ModelServiceProvider(
            name=supported_msp["name"],
            completion_dialect=supported_msp["completion_dialect"],
            embedding_dialect=supported_msp["embedding_dialect"],
            rerank_dialect=supported_msp["rerank_dialect"],
            label=supported_msp["label"],
            allow_custom_base_url=supported_msp["allow_custom_base_url"],
            base_url=supported_msp["base_url"],
        )
        response.append(provider)
    return success(ModelServiceProviderList(items=response))
