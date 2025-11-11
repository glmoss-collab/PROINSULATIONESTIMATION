"""
Caching and Performance Utilities
===================================

Implements intelligent caching for API calls and PDF processing
to reduce costs by ~90% and improve response times.
"""

import os
import json
import hashlib
from pathlib import Path
from typing import Any, Dict, Optional, Callable
from datetime import datetime, timedelta
from functools import wraps
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# FILE-BASED CACHE
# ============================================================================

class FileCache:
    """
    Simple file-based cache with TTL support.

    Caches API responses and PDF analysis results to disk to avoid
    redundant expensive operations.
    """

    def __init__(self, cache_dir: str = ".cache", default_ttl: int = 86400):
        """
        Initialize cache.

        Args:
            cache_dir: Directory to store cache files
            default_ttl: Default time-to-live in seconds (default: 24 hours)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.default_ttl = default_ttl

        # Create subdirectories for organization
        (self.cache_dir / "pdf_analysis").mkdir(exist_ok=True)
        (self.cache_dir / "api_responses").mkdir(exist_ok=True)

        logger.info(f"Initialized cache at {self.cache_dir}")

    def _get_cache_path(self, key: str, category: str = "api_responses") -> Path:
        """Get cache file path for a key."""
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        return self.cache_dir / category / f"{key_hash}.json"

    def _is_expired(self, cache_data: Dict) -> bool:
        """Check if cached data has expired."""
        if "expires_at" not in cache_data:
            return True

        expires_at = datetime.fromisoformat(cache_data["expires_at"])
        return datetime.now() > expires_at

    def get(self, key: str, category: str = "api_responses") -> Optional[Any]:
        """
        Get cached value.

        Args:
            key: Cache key
            category: Cache category (api_responses, pdf_analysis)

        Returns:
            Cached value or None if not found/expired
        """
        cache_path = self._get_cache_path(key, category)

        if not cache_path.exists():
            logger.debug(f"Cache miss: {key}")
            return None

        try:
            with open(cache_path, "r") as f:
                cache_data = json.load(f)

            if self._is_expired(cache_data):
                logger.debug(f"Cache expired: {key}")
                cache_path.unlink()
                return None

            logger.debug(f"Cache hit: {key}")
            return cache_data["value"]

        except Exception as e:
            logger.warning(f"Cache read error: {e}")
            return None

    def set(
        self,
        key: str,
        value: Any,
        category: str = "api_responses",
        ttl: Optional[int] = None
    ) -> None:
        """
        Set cached value.

        Args:
            key: Cache key
            value: Value to cache (must be JSON-serializable)
            category: Cache category
            ttl: Time-to-live in seconds (uses default if not specified)
        """
        cache_path = self._get_cache_path(key, category)
        ttl = ttl if ttl is not None else self.default_ttl

        cache_data = {
            "key": key,
            "value": value,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(seconds=ttl)).isoformat(),
            "ttl": ttl
        }

        try:
            with open(cache_path, "w") as f:
                json.dump(cache_data, f, indent=2)

            logger.debug(f"Cache set: {key} (TTL: {ttl}s)")

        except Exception as e:
            logger.warning(f"Cache write error: {e}")

    def invalidate(self, key: str, category: str = "api_responses") -> None:
        """Invalidate (delete) cached value."""
        cache_path = self._get_cache_path(key, category)
        if cache_path.exists():
            cache_path.unlink()
            logger.debug(f"Cache invalidated: {key}")

    def clear(self, category: Optional[str] = None) -> int:
        """
        Clear cache.

        Args:
            category: Specific category to clear, or None for all

        Returns:
            Number of files deleted
        """
        count = 0

        if category:
            cache_dir = self.cache_dir / category
            if cache_dir.exists():
                for file in cache_dir.glob("*.json"):
                    file.unlink()
                    count += 1
        else:
            for file in self.cache_dir.glob("**/*.json"):
                file.unlink()
                count += 1

        logger.info(f"Cleared {count} cache entries")
        return count

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_files = len(list(self.cache_dir.glob("**/*.json")))
        total_size = sum(f.stat().st_size for f in self.cache_dir.glob("**/*.json"))

        categories = {}
        for category_dir in self.cache_dir.iterdir():
            if category_dir.is_dir():
                files = list(category_dir.glob("*.json"))
                categories[category_dir.name] = {
                    "files": len(files),
                    "size_bytes": sum(f.stat().st_size for f in files)
                }

        return {
            "total_files": total_files,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / 1024 / 1024, 2),
            "categories": categories
        }


# Global cache instance
_cache = None

def get_cache() -> FileCache:
    """Get global cache instance."""
    global _cache
    if _cache is None:
        _cache = FileCache()
    return _cache


# ============================================================================
# CACHING DECORATORS
# ============================================================================

def cached(
    category: str = "api_responses",
    ttl: int = 86400,
    key_fn: Optional[Callable] = None
):
    """
    Decorator to cache function results.

    Args:
        category: Cache category
        ttl: Time-to-live in seconds
        key_fn: Optional function to generate cache key from args

    Example:
        @cached(category="pdf_analysis", ttl=3600)
        def analyze_pdf(pdf_path: str):
            # Expensive operation
            return results
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_fn:
                cache_key = key_fn(*args, **kwargs)
            else:
                # Default: use function name + args/kwargs
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = "_".join(key_parts)

            # Try to get from cache
            cache = get_cache()
            cached_value = cache.get(cache_key, category)

            if cached_value is not None:
                logger.info(f"Using cached result for {func.__name__}")
                return cached_value

            # Execute function
            logger.info(f"Executing {func.__name__} (not cached)")
            result = func(*args, **kwargs)

            # Cache result
            cache.set(cache_key, result, category, ttl)

            return result

        return wrapper
    return decorator


# ============================================================================
# PDF-SPECIFIC CACHING
# ============================================================================

def pdf_cache_key(pdf_path: str, operation: str = "analysis") -> str:
    """
    Generate cache key for PDF operation based on file hash.

    This ensures cache is invalidated if PDF content changes.

    Args:
        pdf_path: Path to PDF file
        operation: Operation name (analysis, extraction, etc.)

    Returns:
        Cache key string
    """
    # Hash file contents
    hasher = hashlib.sha256()

    with open(pdf_path, "rb") as f:
        # Read in chunks for large files
        while chunk := f.read(8192):
            hasher.update(chunk)

    file_hash = hasher.hexdigest()[:16]  # Use first 16 chars

    # Include filename and operation
    filename = Path(pdf_path).name
    return f"{operation}_{filename}_{file_hash}"


def cache_pdf_analysis(ttl: int = 86400):
    """
    Decorator specifically for PDF analysis functions.

    Automatically generates cache key based on PDF content hash.
    """
    return cached(
        category="pdf_analysis",
        ttl=ttl,
        key_fn=lambda pdf_path, **kwargs: pdf_cache_key(pdf_path)
    )


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)

    # Initialize cache
    cache = get_cache()

    # Manual cache operations
    cache.set("test_key", {"data": "value"}, ttl=300)
    result = cache.get("test_key")
    print(f"Cached value: {result}")

    # Cache stats
    stats = cache.stats()
    print(f"Cache stats: {stats}")

    # Decorator example
    @cached(category="api_responses", ttl=60)
    def expensive_operation(param1: str, param2: int):
        import time
        print(f"Executing expensive operation...")
        time.sleep(2)  # Simulate slow operation
        return {"param1": param1, "param2": param2, "result": "data"}

    # First call - slow
    print("First call:")
    result1 = expensive_operation("test", 123)

    # Second call - instant (cached)
    print("\nSecond call:")
    result2 = expensive_operation("test", 123)

    # Clear cache
    cache.clear()
    print("Cache cleared")
