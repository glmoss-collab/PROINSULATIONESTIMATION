"""
Firestore Cache Module
======================

Distributed caching backend using Google Firestore for GCP deployments.
Provides the same interface as FileCache for seamless migration.

Features:
- TTL-based expiration with automatic cleanup
- Distributed access (works across Cloud Run instances)
- Optional Redis layer for faster access
- Memory cache fallback for testing

Usage:
    from firestore_cache import FirestoreCache

    cache = FirestoreCache(project_id="my-project")

    # Set a value
    cache.set("my-key", {"data": "value"}, ttl=3600)

    # Get a value
    result = cache.get("my-key")

    # Use decorator
    @cache.cached(ttl=300)
    def expensive_operation():
        return compute_result()
"""

import os
import json
import hashlib
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Callable, TypeVar
from datetime import datetime, timedelta
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CacheBackend(ABC):
    """Abstract base class for cache backends."""

    @abstractmethod
    def get(self, key: str, category: str = "default") -> Optional[Any]:
        """Get cached value."""
        pass

    @abstractmethod
    def set(
        self,
        key: str,
        value: Any,
        category: str = "default",
        ttl: Optional[int] = None
    ) -> None:
        """Set cached value."""
        pass

    @abstractmethod
    def invalidate(self, key: str, category: str = "default") -> None:
        """Invalidate cached value."""
        pass

    @abstractmethod
    def clear(self, category: Optional[str] = None) -> int:
        """Clear cache."""
        pass

    @abstractmethod
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        pass

    def cached(
        self,
        category: str = "default",
        ttl: int = 3600,
        key_fn: Optional[Callable] = None
    ):
        """Decorator for caching function results."""
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @wraps(func)
            def wrapper(*args, **kwargs) -> T:
                # Generate cache key
                if key_fn:
                    cache_key = key_fn(*args, **kwargs)
                else:
                    key_parts = [func.__name__]
                    key_parts.extend(str(arg) for arg in args)
                    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                    cache_key = "_".join(key_parts)

                # Try cache
                cached_value = self.get(cache_key, category)
                if cached_value is not None:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return cached_value

                # Execute and cache
                logger.debug(f"Cache miss for {func.__name__}")
                result = func(*args, **kwargs)
                self.set(cache_key, result, category, ttl)
                return result

            return wrapper
        return decorator


class MemoryCache(CacheBackend):
    """
    In-memory cache backend.

    Fast but ephemeral - data is lost on restart.
    Useful for testing or as a local cache layer.
    """

    def __init__(self, default_ttl: int = 3600, max_size: int = 1000):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
        self.max_size = max_size
        self._hits = 0
        self._misses = 0
        logger.info(f"MemoryCache initialized (max_size={max_size})")

    def _make_key(self, key: str, category: str) -> str:
        """Create composite key."""
        return f"{category}:{key}"

    def _is_expired(self, entry: Dict) -> bool:
        """Check if entry is expired."""
        if "expires_at" not in entry:
            return True
        expires_at = datetime.fromisoformat(entry["expires_at"])
        return datetime.now() > expires_at

    def _evict_if_needed(self):
        """Evict oldest entries if cache is full."""
        if len(self._cache) >= self.max_size:
            # Remove oldest 10% of entries
            sorted_keys = sorted(
                self._cache.keys(),
                key=lambda k: self._cache[k].get("created_at", "")
            )
            for key in sorted_keys[:max(1, len(sorted_keys) // 10)]:
                del self._cache[key]

    def get(self, key: str, category: str = "default") -> Optional[Any]:
        composite_key = self._make_key(key, category)

        if composite_key not in self._cache:
            self._misses += 1
            return None

        entry = self._cache[composite_key]
        if self._is_expired(entry):
            del self._cache[composite_key]
            self._misses += 1
            return None

        self._hits += 1
        return entry["value"]

    def set(
        self,
        key: str,
        value: Any,
        category: str = "default",
        ttl: Optional[int] = None
    ) -> None:
        self._evict_if_needed()

        composite_key = self._make_key(key, category)
        ttl = ttl if ttl is not None else self.default_ttl

        self._cache[composite_key] = {
            "value": value,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(seconds=ttl)).isoformat(),
            "ttl": ttl
        }

    def invalidate(self, key: str, category: str = "default") -> None:
        composite_key = self._make_key(key, category)
        if composite_key in self._cache:
            del self._cache[composite_key]

    def clear(self, category: Optional[str] = None) -> int:
        if category:
            prefix = f"{category}:"
            keys_to_delete = [k for k in self._cache if k.startswith(prefix)]
            for key in keys_to_delete:
                del self._cache[key]
            return len(keys_to_delete)
        else:
            count = len(self._cache)
            self._cache.clear()
            return count

    def stats(self) -> Dict[str, Any]:
        total = self._hits + self._misses
        return {
            "backend": "memory",
            "entries": len(self._cache),
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self._hits / total, 2) if total > 0 else 0
        }


class FirestoreCache(CacheBackend):
    """
    Google Firestore cache backend.

    Distributed and persistent - works across Cloud Run instances.
    Supports TTL-based automatic expiration.
    """

    def __init__(
        self,
        project_id: Optional[str] = None,
        collection: str = "cache",
        default_ttl: int = 86400
    ):
        try:
            from google.cloud import firestore
        except ImportError:
            raise ImportError(
                "google-cloud-firestore is required for Firestore cache. "
                "Install with: pip install google-cloud-firestore"
            )

        self.project_id = project_id or os.getenv("GCP_PROJECT")
        self.collection_name = collection
        self.default_ttl = default_ttl

        # Initialize Firestore client
        self.db = firestore.Client(project=self.project_id)
        self.collection = self.db.collection(collection)

        self._hits = 0
        self._misses = 0

        logger.info(f"FirestoreCache initialized (project={self.project_id}, collection={collection})")

    def _make_doc_id(self, key: str, category: str) -> str:
        """Create document ID from key and category."""
        # Hash to ensure valid Firestore document ID
        raw = f"{category}:{key}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def _is_expired(self, data: Dict) -> bool:
        """Check if document is expired."""
        if "expires_at" not in data:
            return True

        expires_at = data["expires_at"]
        # Handle Firestore timestamp
        if hasattr(expires_at, 'timestamp'):
            expires_at = datetime.fromtimestamp(expires_at.timestamp())
        elif isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at)

        return datetime.now() > expires_at

    def get(self, key: str, category: str = "default") -> Optional[Any]:
        doc_id = self._make_doc_id(key, category)

        try:
            doc = self.collection.document(doc_id).get()

            if not doc.exists:
                self._misses += 1
                return None

            data = doc.to_dict()

            if self._is_expired(data):
                # Delete expired document
                self.collection.document(doc_id).delete()
                self._misses += 1
                return None

            self._hits += 1

            # Deserialize value
            value = data.get("value")
            if isinstance(value, str):
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return value

        except Exception as e:
            logger.warning(f"Firestore cache get error: {e}")
            self._misses += 1
            return None

    def set(
        self,
        key: str,
        value: Any,
        category: str = "default",
        ttl: Optional[int] = None
    ) -> None:
        doc_id = self._make_doc_id(key, category)
        ttl = ttl if ttl is not None else self.default_ttl

        # Serialize value if needed
        if not isinstance(value, (str, int, float, bool, type(None))):
            serialized_value = json.dumps(value)
        else:
            serialized_value = value

        doc_data = {
            "key": key,
            "category": category,
            "value": serialized_value,
            "created_at": datetime.now(),
            "expires_at": datetime.now() + timedelta(seconds=ttl),
            "ttl": ttl
        }

        try:
            self.collection.document(doc_id).set(doc_data)
            logger.debug(f"Cached {key} in category {category} (TTL: {ttl}s)")
        except Exception as e:
            logger.warning(f"Firestore cache set error: {e}")

    def invalidate(self, key: str, category: str = "default") -> None:
        doc_id = self._make_doc_id(key, category)
        try:
            self.collection.document(doc_id).delete()
            logger.debug(f"Invalidated cache key: {key}")
        except Exception as e:
            logger.warning(f"Firestore cache invalidate error: {e}")

    def clear(self, category: Optional[str] = None) -> int:
        """Clear cache entries. Note: This is expensive for large collections."""
        count = 0

        try:
            if category:
                # Query by category
                docs = self.collection.where("category", "==", category).stream()
            else:
                # Get all documents
                docs = self.collection.stream()

            # Delete in batches
            batch = self.db.batch()
            batch_count = 0

            for doc in docs:
                batch.delete(doc.reference)
                batch_count += 1
                count += 1

                # Commit batch every 500 operations
                if batch_count >= 500:
                    batch.commit()
                    batch = self.db.batch()
                    batch_count = 0

            # Commit remaining
            if batch_count > 0:
                batch.commit()

            logger.info(f"Cleared {count} cache entries")

        except Exception as e:
            logger.warning(f"Firestore cache clear error: {e}")

        return count

    def stats(self) -> Dict[str, Any]:
        total = self._hits + self._misses
        return {
            "backend": "firestore",
            "project": self.project_id,
            "collection": self.collection_name,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self._hits / total, 2) if total > 0 else 0
        }

    def cleanup_expired(self) -> int:
        """
        Cleanup expired entries.

        Call this periodically (e.g., via Cloud Scheduler) to remove
        expired documents and reduce storage costs.
        """
        count = 0

        try:
            # Query for expired documents
            now = datetime.now()
            docs = self.collection.where("expires_at", "<", now).stream()

            # Delete in batches
            batch = self.db.batch()
            batch_count = 0

            for doc in docs:
                batch.delete(doc.reference)
                batch_count += 1
                count += 1

                if batch_count >= 500:
                    batch.commit()
                    batch = self.db.batch()
                    batch_count = 0

            if batch_count > 0:
                batch.commit()

            logger.info(f"Cleaned up {count} expired cache entries")

        except Exception as e:
            logger.warning(f"Firestore cleanup error: {e}")

        return count


class RedisCache(CacheBackend):
    """
    Redis cache backend.

    Fastest option for high-frequency access patterns.
    Use with Google Memorystore for managed Redis in GCP.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        default_ttl: int = 3600
    ):
        try:
            import redis
        except ImportError:
            raise ImportError(
                "redis is required for Redis cache. "
                "Install with: pip install redis"
            )

        self.host = host
        self.port = port
        self.default_ttl = default_ttl

        # Initialize Redis client
        self.client = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True
        )

        self._hits = 0
        self._misses = 0

        logger.info(f"RedisCache initialized ({host}:{port})")

    def _make_key(self, key: str, category: str) -> str:
        """Create Redis key."""
        return f"cache:{category}:{key}"

    def get(self, key: str, category: str = "default") -> Optional[Any]:
        redis_key = self._make_key(key, category)

        try:
            value = self.client.get(redis_key)

            if value is None:
                self._misses += 1
                return None

            self._hits += 1

            # Deserialize
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value

        except Exception as e:
            logger.warning(f"Redis cache get error: {e}")
            self._misses += 1
            return None

    def set(
        self,
        key: str,
        value: Any,
        category: str = "default",
        ttl: Optional[int] = None
    ) -> None:
        redis_key = self._make_key(key, category)
        ttl = ttl if ttl is not None else self.default_ttl

        # Serialize
        serialized = json.dumps(value) if not isinstance(value, str) else value

        try:
            self.client.setex(redis_key, ttl, serialized)
            logger.debug(f"Cached {key} (TTL: {ttl}s)")
        except Exception as e:
            logger.warning(f"Redis cache set error: {e}")

    def invalidate(self, key: str, category: str = "default") -> None:
        redis_key = self._make_key(key, category)
        try:
            self.client.delete(redis_key)
        except Exception as e:
            logger.warning(f"Redis cache invalidate error: {e}")

    def clear(self, category: Optional[str] = None) -> int:
        pattern = f"cache:{category}:*" if category else "cache:*"

        try:
            keys = list(self.client.scan_iter(match=pattern))
            if keys:
                self.client.delete(*keys)
            return len(keys)
        except Exception as e:
            logger.warning(f"Redis cache clear error: {e}")
            return 0

    def stats(self) -> Dict[str, Any]:
        total = self._hits + self._misses
        return {
            "backend": "redis",
            "host": self.host,
            "port": self.port,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self._hits / total, 2) if total > 0 else 0
        }


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

_cache: Optional[CacheBackend] = None


def get_cache() -> CacheBackend:
    """
    Get configured cache backend.

    Returns appropriate backend based on CACHE_BACKEND environment variable.
    """
    global _cache

    if _cache is None:
        backend = os.getenv("CACHE_BACKEND", "file").lower()

        if backend == "firestore":
            _cache = FirestoreCache()
        elif backend == "redis":
            host = os.getenv("REDIS_HOST", "localhost")
            port = int(os.getenv("REDIS_PORT", "6379"))
            _cache = RedisCache(host=host, port=port)
        elif backend == "memory":
            _cache = MemoryCache()
        else:
            # Default to file-based cache (from utils_cache.py)
            from utils_cache import FileCache
            _cache = FileCache()

    return _cache


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Test memory cache
    cache = MemoryCache()

    # Set values
    cache.set("test_key", {"data": "value"}, ttl=300)
    cache.set("another_key", [1, 2, 3], category="lists", ttl=60)

    # Get values
    result = cache.get("test_key")
    print(f"Retrieved: {result}")

    # Use decorator
    @cache.cached(ttl=60)
    def expensive_operation(x: int) -> int:
        print(f"Computing for {x}...")
        return x * 2

    print(expensive_operation(5))  # Computes
    print(expensive_operation(5))  # Uses cache

    # Stats
    print(f"Cache stats: {cache.stats()}")
