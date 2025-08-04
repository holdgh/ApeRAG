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

import fnmatch
import logging
from datetime import datetime
from typing import Any, Dict, Iterator

import boto3
import botocore

from aperag.schema.view_models import CollectionConfig
from aperag.source.base import CustomSourceInitializationError, LocalDocument, RemoteDocument, Source
from aperag.source.utils import gen_temporary_file

logger = logging.getLogger(__name__)


class ObjectStorageSource(Source):
    """
    Generic object storage source that supports S3-compatible APIs.
    Supports filtering objects by include/exclude patterns.
    """

    def __init__(self, ctx: CollectionConfig):
        super().__init__(ctx)
        self.object_storage = ctx.object_storage
        if not self.object_storage:
            raise CustomSourceInitializationError("object_storage configuration is required")
        
        self.endpoint = self.object_storage.endpoint
        self.access_key = self.object_storage.access_key
        self.secret_key = self.object_storage.secret_key
        self.bucket = self.object_storage.bucket
        self.region = self.object_storage.region
        self.enable_path_style = self.object_storage.enable_path_style or False
        self.object_prefix = self.object_storage.object_prefix or ""
        self.include_filters = self.object_storage.include_filters or []
        self.exclude_filters = self.object_storage.exclude_filters or []
        
        # Validate required fields
        if not self.endpoint:
            raise CustomSourceInitializationError("endpoint is required for object storage")
        if not self.access_key:
            raise CustomSourceInitializationError("access_key is required for object storage")
        if not self.secret_key:
            raise CustomSourceInitializationError("secret_key is required for object storage")
        if not self.bucket:
            raise CustomSourceInitializationError("bucket is required for object storage")
        
        self.s3_client = self._connect_s3()

    def _connect_s3(self):
        """Connect to S3-compatible object storage"""
        try:
            # Configure S3 client for custom endpoint
            config = botocore.config.Config(
                connect_timeout=10,
                read_timeout=30,
                s3={
                    'addressing_style': 'path' if self.enable_path_style else 'virtual'
                }
            )
            
            s3_client = boto3.client(
                's3',
                endpoint_url=self.endpoint,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region,
                config=config
            )
            
            # Test connection by checking if bucket exists
            s3_client.head_bucket(Bucket=self.bucket)
            logger.info(f"Successfully connected to object storage bucket: {self.bucket}")
            
            return s3_client
            
        except botocore.exceptions.ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            if error_code == 'NoSuchBucket':
                raise CustomSourceInitializationError(f"Bucket '{self.bucket}' does not exist")
            elif error_code == 'Forbidden':
                raise CustomSourceInitializationError("Access denied. Check your credentials and permissions")
            else:
                raise CustomSourceInitializationError(f"Error connecting to object storage: {error_code}")
        except botocore.exceptions.NoCredentialsError:
            raise CustomSourceInitializationError("Invalid credentials provided")
        except botocore.exceptions.EndpointConnectionError:
            raise CustomSourceInitializationError(f"Unable to connect to endpoint: {self.endpoint}")
        except Exception as e:
            raise CustomSourceInitializationError(f"Error connecting to object storage: {str(e)}")

    def _should_include_object(self, object_key: str) -> bool:
        """
        Check if an object should be included based on include/exclude filters.
        
        Rules:
        1. If include_filters is empty, include all objects
        2. If include_filters is not empty, object must match at least one include pattern
        3. If exclude_filters is not empty, object must not match any exclude pattern
        4. Exclude filters have higher priority than include filters
        
        Args:
            object_key: The object key to check
            
        Returns:
            True if the object should be included, False otherwise
        """
        # Check include filters first
        if self.include_filters:
            # If include filters are specified, object must match at least one
            include_match = any(fnmatch.fnmatch(object_key, pattern) for pattern in self.include_filters)
            if not include_match:
                return False
        
        # Check exclude filters (higher priority)
        if self.exclude_filters:
            # If exclude filters are specified, object must not match any
            exclude_match = any(fnmatch.fnmatch(object_key, pattern) for pattern in self.exclude_filters)
            if exclude_match:
                return False
        
        return True

    def scan_documents(self) -> Iterator[RemoteDocument]:
        """Scan and yield documents from object storage"""
        try:
            logger.info(f"Scanning objects in bucket '{self.bucket}' with prefix '{self.object_prefix}'")
            
            # List objects with pagination
            paginator = self.s3_client.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(
                Bucket=self.bucket,
                Prefix=self.object_prefix
            )
            
            total_objects = 0
            filtered_objects = 0
            
            for page in page_iterator:
                if 'Contents' not in page:
                    continue
                    
                for obj in page['Contents']:
                    total_objects += 1
                    object_key = obj['Key']
                    
                    # Skip directories (objects ending with '/')
                    if object_key.endswith('/'):
                        continue
                    
                    # Apply include/exclude filters
                    if not self._should_include_object(object_key):
                        logger.debug(f"Object '{object_key}' filtered out by include/exclude rules")
                        continue
                    
                    filtered_objects += 1
                    
                    try:
                        # Create document metadata
                        last_modified = obj.get('LastModified')
                        if last_modified:
                            # Convert to UTC timestamp if it's a datetime object
                            if isinstance(last_modified, datetime):
                                modified_time = last_modified
                            else:
                                modified_time = datetime.fromisoformat(str(last_modified).replace('Z', '+00:00'))
                        else:
                            modified_time = None
                        
                        doc = RemoteDocument(
                            name=object_key,
                            size=obj.get('Size', 0),
                            metadata={
                                'modified_time': modified_time,
                                'bucket_name': self.bucket,
                                'etag': obj.get('ETag', '').strip('"'),
                                'storage_class': obj.get('StorageClass', 'STANDARD'),
                            }
                        )
                        
                        logger.debug(f"Found document: {object_key} (size: {obj.get('Size', 0)} bytes)")
                        yield doc
                        
                    except Exception as e:
                        logger.error(f"Error processing object '{object_key}': {e}")
                        continue
            
            logger.info(f"Scan completed. Total objects: {total_objects}, Filtered objects: {filtered_objects}")
            
        except Exception as e:
            logger.error(f"Error scanning objects in bucket '{self.bucket}': {e}")
            raise CustomSourceInitializationError(f"Error scanning objects: {str(e)}")

    def prepare_document(self, name: str, metadata: Dict[str, Any]) -> LocalDocument:
        """Download and prepare a document for processing"""
        try:
            logger.debug(f"Downloading object: {name}")
            
            # Download object from S3
            response = self.s3_client.get_object(Bucket=self.bucket, Key=name)
            content = response['Body'].read()
            
            # Create temporary file
            temp_file = gen_temporary_file(name)
            temp_file.write(content)
            temp_file.close()
            
            # Update metadata
            metadata = metadata.copy()
            metadata['name'] = name
            metadata['source_type'] = 'object_storage'
            metadata['endpoint'] = self.endpoint
            metadata['bucket'] = self.bucket
            
            logger.debug(f"Downloaded object '{name}' to temporary file: {temp_file.name}")
            
            return LocalDocument(
                name=name,
                path=temp_file.name,
                size=len(content),
                metadata=metadata
            )
            
        except botocore.exceptions.ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            if error_code == 'NoSuchKey':
                raise CustomSourceInitializationError(f"Object '{name}' not found in bucket '{self.bucket}'")
            else:
                raise CustomSourceInitializationError(f"Error downloading object '{name}': {error_code}")
        except Exception as e:
            logger.error(f"Error preparing document '{name}': {e}")
            raise CustomSourceInitializationError(f"Error preparing document '{name}': {str(e)}")

    def sync_enabled(self):
        """Object storage supports synchronization"""
        return True

    def close(self):
        """Clean up resources"""
        # boto3 clients don't need explicit closing
        pass
