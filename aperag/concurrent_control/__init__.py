"""
Universal Concurrent Control Module

This module provides unified concurrent control mechanisms for any application.
It supports different lock implementations based on deployment scenarios:

- ThreadingLock: For single-process environments (solo, threads, gevent)
- RedisLock: For multi-process environments (prefork, distributed deployment)

The lock choice and configuration are passed as parameters rather than environment variables,
making it more flexible and reusable across different projects and components.
"""

from .core import (
    LockProtocol,
    ThreadingLock,
    RedisLock,
    LockManager,
    create_lock,
    lock_context,
    get_default_lock_manager,
)

__all__ = [
    "LockProtocol",
    "ThreadingLock", 
    "RedisLock",
    "LockManager",
    "create_lock",
    "lock_context",
    "get_default_lock_manager",
]

__version__ = "1.0.0" 