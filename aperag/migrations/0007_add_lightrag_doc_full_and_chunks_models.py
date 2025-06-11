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

"""Add LightRAG all tables

Revision ID: 0007
Revises: 0006
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0007'
down_revision = '0006'
branch_labels = None
depends_on = None


def upgrade():
    # Ensure pgvector extension is enabled
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Create LIGHTRAG_DOC_FULL table
    op.execute('''CREATE TABLE LIGHTRAG_DOC_FULL
    (
        id VARCHAR(255),
        workspace VARCHAR(255),
        doc_name VARCHAR(1024),
        content TEXT,
        meta JSONB,
        create_time TIMESTAMP(0),
        update_time TIMESTAMP(0),
        CONSTRAINT LIGHTRAG_DOC_FULL_PK PRIMARY KEY (workspace, id)
    )''')

    # Create LIGHTRAG_DOC_CHUNKS table
    op.execute('''CREATE TABLE LIGHTRAG_DOC_CHUNKS
    (
        id VARCHAR(255),
        workspace VARCHAR(255),
        full_doc_id VARCHAR(256),
        chunk_order_index INTEGER,
        tokens INTEGER,
        content TEXT,
        content_vector VECTOR,
        file_path VARCHAR(256),
        create_time TIMESTAMP(0) WITH TIME ZONE,
        update_time TIMESTAMP(0) WITH TIME ZONE,
        CONSTRAINT LIGHTRAG_DOC_CHUNKS_PK PRIMARY KEY (workspace, id)
    )''')

    # Create LIGHTRAG_VDB_ENTITY table
    op.execute('''CREATE TABLE LIGHTRAG_VDB_ENTITY
    (
        id             VARCHAR(255),
        workspace      VARCHAR(255),
        entity_name    VARCHAR(255),
        content        TEXT,
        content_vector VECTOR,
        create_time    TIMESTAMP(0) WITH TIME ZONE,
        update_time    TIMESTAMP(0) WITH TIME ZONE,
        chunk_ids      VARCHAR(255)[] NULL,
        file_path      TEXT NULL,
        CONSTRAINT LIGHTRAG_VDB_ENTITY_PK PRIMARY KEY (workspace, id)
    )''')

    # Create LIGHTRAG_VDB_RELATION table
    op.execute('''CREATE TABLE LIGHTRAG_VDB_RELATION
    (
        id             VARCHAR(255),
        workspace      VARCHAR(255),
        source_id      VARCHAR(256),
        target_id      VARCHAR(256),
        content        TEXT,
        content_vector VECTOR,
        create_time    TIMESTAMP(0) WITH TIME ZONE,
        update_time    TIMESTAMP(0) WITH TIME ZONE,
        chunk_ids      VARCHAR(255)[] NULL,
        file_path      TEXT NULL,
        CONSTRAINT LIGHTRAG_VDB_RELATION_PK PRIMARY KEY (workspace, id)
    )''')

    # Create LIGHTRAG_LLM_CACHE table
    op.execute('''CREATE TABLE LIGHTRAG_LLM_CACHE (
        workspace varchar(255) NOT NULL,
        id varchar(255) NOT NULL,
        mode varchar(32) NOT NULL,
        original_prompt TEXT,
        return_value TEXT,
        create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        update_time TIMESTAMP,
        CONSTRAINT LIGHTRAG_LLM_CACHE_PK PRIMARY KEY (workspace, mode, id)
    )''')

    # Note: LIGHTRAG_DOC_STATUS table already exists from previous migration 0006

    # Add indexes for better performance
    op.create_index('idx_lightrag_doc_full_workspace', 'lightrag_doc_full', ['workspace'])
    op.create_index('idx_lightrag_doc_chunks_workspace', 'lightrag_doc_chunks', ['workspace'])
    op.create_index('idx_lightrag_doc_chunks_full_doc_id', 'lightrag_doc_chunks', ['full_doc_id'])
    op.create_index('idx_lightrag_vdb_entity_workspace', 'lightrag_vdb_entity', ['workspace'])
    op.create_index('idx_lightrag_vdb_entity_entity_name', 'lightrag_vdb_entity', ['entity_name'])
    op.create_index('idx_lightrag_vdb_relation_workspace', 'lightrag_vdb_relation', ['workspace'])
    op.create_index('idx_lightrag_vdb_relation_source_target', 'lightrag_vdb_relation', ['source_id', 'target_id'])
    op.create_index('idx_lightrag_llm_cache_workspace', 'lightrag_llm_cache', ['workspace'])


def downgrade():
    # Drop indexes first
    op.drop_index('idx_lightrag_llm_cache_workspace', 'lightrag_llm_cache')
    op.drop_index('idx_lightrag_vdb_relation_source_target', 'lightrag_vdb_relation')
    op.drop_index('idx_lightrag_vdb_relation_workspace', 'lightrag_vdb_relation')
    op.drop_index('idx_lightrag_vdb_entity_entity_name', 'lightrag_vdb_entity')
    op.drop_index('idx_lightrag_vdb_entity_workspace', 'lightrag_vdb_entity')
    op.drop_index('idx_lightrag_doc_chunks_full_doc_id', 'lightrag_doc_chunks')
    op.drop_index('idx_lightrag_doc_chunks_workspace', 'lightrag_doc_chunks')
    op.drop_index('idx_lightrag_doc_full_workspace', 'lightrag_doc_full')
    
    # Drop tables
    op.execute('DROP TABLE LIGHTRAG_LLM_CACHE')
    op.execute('DROP TABLE LIGHTRAG_VDB_RELATION')
    op.execute('DROP TABLE LIGHTRAG_VDB_ENTITY')
    op.execute('DROP TABLE LIGHTRAG_DOC_CHUNKS')
    op.execute('DROP TABLE LIGHTRAG_DOC_FULL') 