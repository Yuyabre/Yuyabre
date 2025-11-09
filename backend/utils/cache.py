"""
Cache utility for database queries using LRU cache.

Provides async-compatible LRU caching with automatic invalidation on writes.
"""
from functools import wraps
from typing import Any, Callable, Dict, Optional
from collections import OrderedDict
import inspect
import asyncio
from loguru import logger


class AsyncLRUCache:
    """
    Thread-safe async LRU cache implementation.
    
    This is a custom implementation because Python's functools.lru_cache
    doesn't work with async functions.
    """
    
    def __init__(self, maxsize: int = 128):
        """
        Initialize the cache.
        
        Args:
            maxsize: Maximum number of items to cache
        """
        self.maxsize = maxsize
        self.cache: OrderedDict[str, Any] = OrderedDict()
        self.lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        async with self.lock:
            if key in self.cache:
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                logger.debug(f"Cache hit: {key}")
                return self.cache[key]
            logger.debug(f"Cache miss: {key}")
            return None
    
    async def set(self, key: str, value: Any) -> None:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        async with self.lock:
            if key in self.cache:
                # Update existing and move to end
                self.cache.move_to_end(key)
                self.cache[key] = value
            else:
                # Add new item
                self.cache[key] = value
                # Evict oldest if over maxsize
                if len(self.cache) > self.maxsize:
                    oldest_key = next(iter(self.cache))
                    del self.cache[oldest_key]
                    logger.debug(f"Cache evicted: {oldest_key}")
            logger.debug(f"Cache set: {key}")
    
    async def clear(self) -> None:
        """Clear all cached items."""
        async with self.lock:
            count = len(self.cache)
            self.cache.clear()
            logger.info(f"Cache cleared: {count} items removed")
    
    async def invalidate(self, pattern: Optional[str] = None) -> int:
        """
        Invalidate cache entries matching a pattern.
        
        Args:
            pattern: Optional pattern to match keys. If None, clears all.
            
        Returns:
            Number of items invalidated
        """
        async with self.lock:
            if pattern is None:
                count = len(self.cache)
                self.cache.clear()
                logger.info(f"Cache invalidated: all {count} items")
                return count
            
            # Remove keys matching pattern
            keys_to_remove = [
                key for key in self.cache.keys()
                if pattern in key
            ]
            for key in keys_to_remove:
                del self.cache[key]
            
            logger.info(f"Cache invalidated: {len(keys_to_remove)} items matching '{pattern}'")
            return len(keys_to_remove)
    
    async def size(self) -> int:
        """Get current cache size."""
        return len(self.cache)


# Global cache instances for different services
_inventory_cache: Optional[AsyncLRUCache] = None
_order_cache: Optional[AsyncLRUCache] = None


def get_inventory_cache() -> AsyncLRUCache:
    """Get or create the inventory cache instance."""
    global _inventory_cache
    if _inventory_cache is None:
        _inventory_cache = AsyncLRUCache(maxsize=256)
    return _inventory_cache


def get_order_cache() -> AsyncLRUCache:
    """Get or create the order cache instance."""
    global _order_cache
    if _order_cache is None:
        _order_cache = AsyncLRUCache(maxsize=128)
    return _order_cache


def cached_query(cache_key_prefix: str, cache_instance: Callable[[], AsyncLRUCache]):
    """
    Decorator to cache async query results.
    
    Args:
        cache_key_prefix: Prefix for cache keys (e.g., "inventory", "order")
        cache_instance: Function that returns the cache instance
        
    Usage:
        @cached_query("inventory", get_inventory_cache)
        async def get_all_items(self):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get function signature to map positional args to parameter names
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Generate cache key from function name and arguments
            key_parts = [cache_key_prefix, func.__name__]
            
            # Add all arguments to key (skip self)
            for param_name, param_value in sorted(bound_args.arguments.items()):
                if param_name != 'self' and param_value is not None:
                    key_parts.append(f"{param_name}:{param_value}")
            
            cache_key = "|".join(key_parts)
            cache = cache_instance()
            
            # Try to get from cache
            cached_result = await cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result)
            return result
        
        return wrapper
    return decorator

