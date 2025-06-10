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

from django.db import migrations, models


class Migration(migrations.Migration):
    
    dependencies = [
        ('aperag', '0005_execute_model_configs_sql'),
    ]

    operations = [
        # Create LightRAG document status table
        migrations.RunSQL(
            sql="""
            CREATE TABLE IF NOT EXISTS lightrag_doc_status (
                workspace VARCHAR(255) NOT NULL,
                id VARCHAR(255) NOT NULL,
                content TEXT,
                content_summary VARCHAR(255),
                content_length INTEGER,
                chunks_count INTEGER,
                status VARCHAR(64),
                file_path TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT uq_lightrag_doc_status_workspace_id UNIQUE (workspace, id),
                PRIMARY KEY (workspace, id)
            );
            
            -- Create index on status for better query performance
            CREATE INDEX IF NOT EXISTS idx_lightrag_doc_status_workspace_status 
            ON lightrag_doc_status(workspace, status);
            """,
            reverse_sql="""
            DROP TABLE IF EXISTS lightrag_doc_status;
            """,
        ),
    ] 