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

from fastapi import APIRouter, Depends, HTTPException, Query

from aperag.db.models import User
from aperag.exceptions import CollectionMarketplaceAccessDeniedError
from aperag.schema import view_models
from aperag.service.marketplace_collection_service import marketplace_collection_service
from aperag.views.auth import current_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["marketplace-collections"])


@router.get("/marketplace/collections/{collection_id}", response_model=view_models.SharedCollection)
async def get_marketplace_collection(
    collection_id: str,
    user: User = Depends(current_user),
) -> view_models.SharedCollection:
    """Get MarketplaceCollection details (read-only)"""
    try:
        result = await marketplace_collection_service.get_marketplace_collection(user.id, collection_id)
        return result
    except CollectionMarketplaceAccessDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting marketplace collection {collection_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/marketplace/collections/{collection_id}/documents", response_model=view_models.DocumentList)
async def list_marketplace_collection_documents(
    collection_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str = Query(None),
    file_type: str = Query(None),
    user: User = Depends(current_user),
) -> view_models.DocumentList:
    """List documents in MarketplaceCollection (read-only)"""
    try:
        result = await marketplace_collection_service.list_marketplace_collection_documents(
            user.id, collection_id, page, page_size, search, file_type
        )
        return result
    except CollectionMarketplaceAccessDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error listing marketplace collection documents {collection_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/marketplace/collections/{collection_id}/documents/{document_id}/preview",
    response_model=view_models.DocumentPreview,
)
async def get_marketplace_collection_document_preview(
    collection_id: str,
    document_id: str,
    user: User = Depends(current_user),
) -> view_models.DocumentPreview:
    """Preview document in MarketplaceCollection (read-only)"""
    try:
        result = await marketplace_collection_service.get_marketplace_collection_document_preview(
            user.id, collection_id, document_id
        )
        return result
    except CollectionMarketplaceAccessDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting marketplace collection document preview {collection_id}/{document_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/marketplace/collections/{collection_id}/graph")
async def get_marketplace_collection_graph(
    collection_id: str,
    node_limit: int = Query(100, ge=1, le=1000),
    depth: int = Query(2, ge=1, le=5),
    user: User = Depends(current_user),
) -> Dict[str, Any]:
    """Get knowledge graph for MarketplaceCollection (read-only)"""
    try:
        result = await marketplace_collection_service.get_marketplace_collection_graph(
            user.id, collection_id, node_limit=node_limit, depth=depth
        )
        # Add read_only flag to indicate this is read-only access
        result["read_only"] = True
        return result
    except CollectionMarketplaceAccessDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting marketplace collection graph {collection_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
