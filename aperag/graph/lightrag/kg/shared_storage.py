import asyncio
import os
import sys
import logging

logger = logging.getLogger(__name__)


def direct_log(message, level="INFO", enable_output: bool = True):
    """
    Log a message directly to stderr to ensure visibility.

    Args:
        message: The message to log
        level: Log level (default: "INFO")
        enable_output: Whether to actually output the log (default: True)
    """
    if enable_output:
        print(f"{level}: {message}", file=sys.stderr, flush=True)


# Global state for essential locks only
_initialized = None
_graph_db_lock: asyncio.Lock | None = None


def get_graph_db_lock() -> asyncio.Lock:
    """Return graph database lock for ensuring atomic operations"""
    return _graph_db_lock


def initialize_share_data():
    """
    Initialize essential locks for async operations.
    """
    global _graph_db_lock, _initialized

    # Check if already initialized
    if _initialized:
        direct_log(f"Process {os.getpid()} locks already initialized")
        return

    _graph_db_lock = asyncio.Lock()
    
    direct_log(f"Process {os.getpid()} essential locks created")

    # Mark as initialized
    _initialized = True


