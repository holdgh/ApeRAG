#!/usr/bin/env python3
"""
Script to generate SQL upsert statements from model_configs.json

This script reads the model_configs.json file and generates PostgreSQL
upsert statements to populate the aperag_llm_provider and 
aperag_llm_provider_models tables.

Usage:
    python generate_model_config_sql.py

Output:
    SQL script with upsert statements written to model_configs_init.sql
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional


def escape_sql_string(value: str) -> str:
    """Escape single quotes in SQL strings"""
    if value is None:
        return 'NULL'
    return f"'{value.replace(chr(39), chr(39) + chr(39))}'"


def format_boolean(value: bool) -> str:
    """Format boolean for PostgreSQL"""
    return 'TRUE' if value else 'FALSE'


def format_nullable_int(value: Optional[int]) -> str:
    """Format nullable integer for PostgreSQL"""
    return str(value) if value is not None else 'NULL'


def generate_provider_upsert(provider: Dict[str, Any]) -> str:
    """Generate upsert statement for aperag_llm_provider table"""
    
    name = escape_sql_string(provider['name'])
    label = escape_sql_string(provider['label'])
    completion_dialect = escape_sql_string(provider['completion_dialect'])
    embedding_dialect = escape_sql_string(provider['embedding_dialect'])
    rerank_dialect = escape_sql_string(provider['rerank_dialect'])
    allow_custom_base_url = format_boolean(provider['allow_custom_base_url'])
    base_url = escape_sql_string(provider['base_url'])
    
    return f"""INSERT INTO aperag_llm_provider (
    name, label, completion_dialect, embedding_dialect, rerank_dialect, 
    allow_custom_base_url, base_url, gmt_created, gmt_updated
) VALUES (
    {name}, {label}, {completion_dialect}, {embedding_dialect}, {rerank_dialect}, 
    {allow_custom_base_url}, {base_url}, NOW(), NOW()
)
ON CONFLICT (name) DO UPDATE SET
    label = EXCLUDED.label,
    completion_dialect = EXCLUDED.completion_dialect,
    embedding_dialect = EXCLUDED.embedding_dialect,
    rerank_dialect = EXCLUDED.rerank_dialect,
    allow_custom_base_url = EXCLUDED.allow_custom_base_url,
    base_url = EXCLUDED.base_url,
    gmt_updated = NOW();"""


def format_json_array(value: List[str]) -> str:
    """Format list as JSON array for PostgreSQL"""
    if not value:
        return "'[]'::jsonb"
    # Convert list to JSON string and escape it for SQL
    import json
    json_str = json.dumps(value)
    return f"'{json_str}'::jsonb"


def generate_model_upserts(provider_name: str, api_type: str, models: List[Dict[str, Any]]) -> List[str]:
    """Generate upsert statements for aperag_llm_provider_models table"""
    
    upserts = []
    for model in models:
        provider_name_sql = escape_sql_string(provider_name)
        api_sql = escape_sql_string(api_type)
        model_name_sql = escape_sql_string(model['model'])
        custom_llm_provider_sql = escape_sql_string(model['custom_llm_provider'])
        max_tokens_sql = format_nullable_int(model.get('max_tokens'))
        
        # Handle tags - for now, we'll set reasonable defaults based on provider and model
        tags = model.get('tags', [])
        if not tags:
            # Set default tags based on model characteristics
            tags = []
            model_name = model['model'].lower()
            
            # Add 'free' tag for free models
            if ':free' in model_name or provider_name in ['openrouter']:
                tags.append('free')
            
            # Add 'recommend' tag for popular models
            if any(keyword in model_name for keyword in ['gpt-4o', 'claude-3-5', 'gemini-2.5', 'qwen-max', 'deepseek-r1']):
                tags.append('recommend')
        
        tags_sql = format_json_array(tags)
        
        upsert = f"""INSERT INTO aperag_llm_provider_models (
    provider_name, api, model, custom_llm_provider, max_tokens, tags,
    gmt_created, gmt_updated
) VALUES (
    {provider_name_sql}, {api_sql}, {model_name_sql}, {custom_llm_provider_sql}, {max_tokens_sql}, {tags_sql},
    NOW(), NOW()
)
ON CONFLICT (provider_name, api, model) DO UPDATE SET
    custom_llm_provider = EXCLUDED.custom_llm_provider,
    max_tokens = EXCLUDED.max_tokens,
    tags = EXCLUDED.tags,
    gmt_updated = NOW();"""
        
        upserts.append(upsert)
    
    return upserts


def generate_sql_script() -> str:
    """Generate complete SQL script from model_configs.json"""
    
    # Check if model_configs.json exists
    config_file = '../model_configs.json'
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Could not find {config_file} in current directory")
    
    # Read and parse JSON
    with open(config_file, 'r', encoding='utf-8') as f:
        providers_data = json.load(f)
    
    # Generate SQL header
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    sql_lines = [
        "-- Model configuration initialization SQL script",
        f"-- Generated from model_configs.json on {timestamp}",
        "-- This script populates aperag_llm_provider and aperag_llm_provider_models tables",
        "",
        "BEGIN;",
        "",
        "-- Insert/Update LLM Providers",
        ""
    ]
    
    # Generate provider upserts
    for provider in providers_data:
        sql_lines.append(f"-- Provider: {provider['name']}")
        sql_lines.append(generate_provider_upsert(provider))
        sql_lines.append("")
    
    sql_lines.extend([
        "-- Insert/Update Provider Models",
        ""
    ])
    
    # Generate model upserts
    for provider in providers_data:
        provider_name = provider['name']
        
        # Process completion models
        if 'completion' in provider and provider['completion']:
            sql_lines.append(f"-- Completion models for {provider_name}")
            for upsert in generate_model_upserts(provider_name, 'completion', provider['completion']):
                sql_lines.append(upsert)
                sql_lines.append("")
        
        # Process embedding models
        if 'embedding' in provider and provider['embedding']:
            sql_lines.append(f"-- Embedding models for {provider_name}")
            for upsert in generate_model_upserts(provider_name, 'embedding', provider['embedding']):
                sql_lines.append(upsert)
                sql_lines.append("")
        
        # Process rerank models
        if 'rerank' in provider and provider['rerank']:
            sql_lines.append(f"-- Rerank models for {provider_name}")
            for upsert in generate_model_upserts(provider_name, 'rerank', provider['rerank']):
                sql_lines.append(upsert)
                sql_lines.append("")
    
    sql_lines.extend([
        "COMMIT;",
        "",
        f"-- Script completed. Generated on {timestamp}",
        f"-- Total providers: {len(providers_data)}",
        f"-- Total models: {sum(len(p.get('completion', [])) + len(p.get('embedding', [])) + len(p.get('rerank', [])) for p in providers_data)}"
    ])
    
    return "\n".join(sql_lines)


def main():
    """Main function to generate and save SQL script"""
    try:
        print("Reading model_configs.json...")
        sql_script = generate_sql_script()
        
        output_file = 'model_configs_init.sql'
        print(f"Writing SQL script to {output_file}...")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(sql_script)
        
        print(f"✅ SQL script generated successfully: {output_file}")
        print("\nTo execute the script:")
        print(f"  psql -h <host> -U <user> -d <database> -f {output_file}")
        print("\nOr copy the contents and run in your PostgreSQL client.")
        
    except Exception as e:
        print(f"❌ Error generating SQL script: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 