"""Cache management for embeddings and frequently accessed data."""

import os
import json
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Manages caching of embeddings and other frequently accessed data.
    Supports file-based and in-memory caching strategies.
    """
    
    def __init__(self, cache_dir: str = "./cache"):
        """
        Initialize cache manager.
        
        Args:
            cache_dir: Directory for storing cache files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.memory_cache: Dict[str, Any] = {}
    
    def _generate_key(self, content: str) -> str:
        """
        Generate cache key from content.
        
        Args:
            content: Content to hash
        
        Returns:
            MD5 hash of content
        """
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, key: str, use_memory: bool = True) -> Optional[Any]:
        """
        Retrieve value from cache.
        
        Args:
            key: Cache key
            use_memory: Check memory cache first
        
        Returns:
            Cached value or None
        """
        # Check memory cache first
        if use_memory and key in self.memory_cache:
            logger.debug(f"Cache hit (memory): {key}")
            return self.memory_cache[key]
        
        # Check file cache
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    value = json.load(f)
                    if use_memory:
                        self.memory_cache[key] = value
                    logger.debug(f"Cache hit (file): {key}")
                    return value
            except Exception as e:
                logger.warning(f"Error reading cache file {key}: {str(e)}")
        
        logger.debug(f"Cache miss: {key}")
        return None
    
    def set(self, key: str, value: Any, use_memory: bool = True) -> bool:
        """
        Store value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            use_memory: Also store in memory cache
        
        Returns:
            True if successful
        """
        try:
            # Store in memory cache
            if use_memory:
                self.memory_cache[key] = value
            
            # Store in file cache
            cache_file = self.cache_dir / f"{key}.json"
            with open(cache_file, 'w') as f:
                json.dump(value, f)
            
            logger.debug(f"Cache set: {key}")
            return True
        except Exception as e:
            logger.error(f"Error setting cache {key}: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete cached value.
        
        Args:
            key: Cache key to delete
        
        Returns:
            True if successful
        """
        try:
            if key in self.memory_cache:
                del self.memory_cache[key]
            
            cache_file = self.cache_dir / f"{key}.json"
            if cache_file.exists():
                cache_file.unlink()
            
            logger.debug(f"Cache deleted: {key}")
            return True
        except Exception as e:
            logger.error(f"Error deleting cache {key}: {str(e)}")
            return False
    
    def clear(self) -> bool:
        """
        Clear all cached values.
        
        Returns:
            True if successful
        """
        try:
            self.memory_cache.clear()
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
            logger.info("Cache cleared")
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            return False
    
    def get_cache_size(self) -> dict:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache size information
        """
        memory_size = len(self.memory_cache)
        file_count = len(list(self.cache_dir.glob("*.json")))
        total_size = sum(f.stat().st_size for f in self.cache_dir.glob("*.json"))
        
        return {
            "memory_items": memory_size,
            "file_items": file_count,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / 1024 / 1024, 2)
        }
