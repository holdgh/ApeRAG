CREATE TABLE LIGHTRAG_DOC_FULL
(
    id VARCHAR(255),
    workspace VARCHAR(255),
    doc_name VARCHAR(1024),
    content TEXT,
    meta JSONB,
    create_time TIMESTAMP(0),
    update_time TIMESTAMP(0),
    CONSTRAINT LIGHTRAG_DOC_FULL_PK PRIMARY KEY (workspace, id)
);

CREATE TABLE LIGHTRAG_DOC_CHUNKS
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
);

CREATE TABLE LIGHTRAG_VDB_ENTITY
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
);

CREATE TABLE LIGHTRAG_VDB_RELATION
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
);

CREATE TABLE LIGHTRAG_LLM_CACHE (
    workspace varchar(255) NOT NULL,
    id varchar(255) NOT NULL,
    mode varchar(32) NOT NULL,
    original_prompt TEXT,
    return_value TEXT,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP,
    CONSTRAINT LIGHTRAG_LLM_CACHE_PK PRIMARY KEY (workspace, mode, id)
);

CREATE TABLE LIGHTRAG_DOC_STATUS
(
    workspace       varchar(255) NOT NULL,
    id              varchar(255) NOT NULL,
    content         TEXT NULL,
    content_summary varchar(255) NULL,
    content_length  int4 NULL,
    chunks_count    int4 NULL,
    status          varchar(64) NULL,
    file_path       TEXT NULL,
    created_at      timestamp with time zone DEFAULT CURRENT_TIMESTAMP NULL,
    updated_at      timestamp with time zone DEFAULT CURRENT_TIMESTAMP NULL,
    CONSTRAINT LIGHTRAG_DOC_STATUS_PK PRIMARY KEY (workspace, id)
);