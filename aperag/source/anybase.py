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

import logging
from typing import Any, Dict

from aperag.config import settings
from aperag.schema.view_models import CollectionConfig, ObjectStorage
from aperag.source.base import CustomSourceInitializationError
from aperag.source.object_storage import ObjectStorageSource

logger = logging.getLogger(__name__)


class AnybaseSource(ObjectStorageSource):
    """
    Anybase object storage source that uses environment variables for connection configuration.
    Inherits from ObjectStorageSource and overrides initialization to use environment variables.
    """

    def __init__(self, ctx: CollectionConfig):
        # Validate anybase configuration
        if not ctx.anybase:
            raise CustomSourceInitializationError("anybase configuration is required")
        
        # Get connection parameters from environment variables via settings
        if not settings.anybase_config:
            raise CustomSourceInitializationError("anybase_config is not initialized in settings")
        
        # Validate required environment variables
        if not settings.anybase_config.endpoint:
            raise CustomSourceInitializationError("ANYBASE_ENDPOINT environment variable is required")
        if not settings.anybase_config.access_key:
            raise CustomSourceInitializationError("ANYBASE_ACCESS_KEY environment variable is required")
        if not settings.anybase_config.secret_key:
            raise CustomSourceInitializationError("ANYBASE_SECRET_KEY environment variable is required")
        if not settings.anybase_config.bucket:
            raise CustomSourceInitializationError("ANYBASE_BUCKET environment variable is required")
        
        # Create object_storage config from environment variables and user input
        object_storage_config = ObjectStorage(
            endpoint=settings.anybase_config.endpoint,
            access_key=settings.anybase_config.access_key,
            secret_key=settings.anybase_config.secret_key,
            bucket=settings.anybase_config.bucket,
            region=settings.anybase_config.region,
            enable_path_style=settings.anybase_config.use_path_style,
            object_prefix=ctx.anybase.object_prefix or "",
            include_filters=ctx.anybase.include_filters or [],
            exclude_filters=ctx.anybase.exclude_filters or []
        )
        
        # Create a new CollectionConfig with object_storage instead of anybase
        modified_ctx = CollectionConfig(
            source="object_storage",
            object_storage=object_storage_config,
            # Copy other fields from original config
            crontab=ctx.crontab,
            enable_knowledge_graph=ctx.enable_knowledge_graph,
            enable_summary=ctx.enable_summary,
            enable_vision=ctx.enable_vision,
            embedding=ctx.embedding,
            completion=ctx.completion,
            system=ctx.system
        )
        
        # Initialize parent class with modified config
        super().__init__(modified_ctx)
        
        logger.info(f"Successfully initialized anybase source using endpoint: {settings.anybase_config.endpoint}, bucket: {settings.anybase_config.bucket}")

    def prepare_document(self, name: str, metadata: Dict[str, Any]) -> Any:
        """Override to set source_type to 'anybase'"""
        local_doc = super().prepare_document(name, metadata)
        # Update metadata to indicate this is from anybase
        local_doc.metadata['source_type'] = 'anybase'
        return local_doc
