#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

# Load environment variables from file using the most robust method
# This uses the widely recommended "set -a; source file; set +a" approach
load_env_from_file() {
    local env_file="${1:-${ENV_CONFIG_FILE:-/app/env-config/.env}}"
    
    if [ ! -f "$env_file" ]; then
        echo "Info: Environment file $env_file not found, skipping"
        return 0
    fi
    
    if [ ! -r "$env_file" ]; then
        echo "Error: Cannot read environment file $env_file"
        return 1
    fi
    
    echo "Loading environment variables from $env_file"
    
    # Count variables before loading
    local vars_before=$(env | wc -l)
    
    # Use the most robust method: set -a enables auto-export, source loads the file
    # This handles all edge cases including quotes, spaces, special characters, etc.
    set -a
    source "$env_file"
    set +a
    
    # Count variables after loading
    local vars_after=$(env | wc -l)
    local loaded_count=$((vars_after - vars_before))
    
    echo "Environment variables loaded successfully: $loaded_count new variables"
    return 0
}

# Load environment variables from config file
# Allow override via ENV_CONFIG_FILE environment variable
if ! load_env_from_file; then
    echo "Failed to load environment variables, exiting"
    exit 1
fi

python3 << END
import sys
import time

import psycopg2

suggest_unrecoverable_after = 30
start = time.time()

while True:
    try:
        psycopg2.connect(
            dbname="${POSTGRES_DB}",
            user="${POSTGRES_USER}",
            password="${POSTGRES_PASSWORD}",
            host="${POSTGRES_HOST}",
            port="${POSTGRES_PORT}",
        )
        break
    except psycopg2.OperationalError as error:
        sys.stderr.write("Waiting for PostgreSQL to become available...\n")

        if time.time() - start > suggest_unrecoverable_after:
            sys.stderr.write("  This is taking longer than expected. The following exception may be indicative of an unrecoverable error: '{}'\n".format(error))

    time.sleep(1)
END

>&2 echo 'PostgreSQL is available'

exec "$@"
