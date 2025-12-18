"""
Cloud Configuration Module
===========================

Centralized configuration management for GCP enterprise deployment.
Automatically detects environment (local vs GCP) and configures
appropriate backends for caching, storage, and secrets.

Usage:
    from cloud_config import config

    # Get API key (from env var locally, Secret Manager in GCP)
    api_key = config.get_anthropic_api_key()

    # Get configured cache backend
    cache = config.get_cache_backend()

    # Get configured storage backend
    storage = config.get_storage_backend()
"""

import os
import logging
from enum import Enum
from typing import Optional, Any, Dict
from dataclasses import dataclass, field
from functools import lru_cache

logger = logging.getLogger(__name__)


class Environment(Enum):
    """Deployment environment."""
    LOCAL = "local"
    GCP_STAGING = "staging"
    GCP_PRODUCTION = "production"


class CacheBackend(Enum):
    """Available cache backends."""
    FILE = "file"           # Local file-based (default for local dev)
    FIRESTORE = "firestore" # Google Firestore (recommended for GCP)
    REDIS = "redis"         # Redis Memorystore (optional, fastest)
    MEMORY = "memory"       # In-memory only (ephemeral, for testing)


class StorageBackend(Enum):
    """Available storage backends."""
    LOCAL = "local"  # Local filesystem (default for local dev)
    GCS = "gcs"      # Google Cloud Storage (recommended for GCP)


@dataclass
class CloudConfig:
    """
    Centralized cloud configuration.

    Automatically detects GCP environment and configures
    appropriate backends and credentials.
    """

    # Environment detection
    gcp_project: Optional[str] = field(default=None)
    environment: Environment = field(default=Environment.LOCAL)

    # Backend configuration
    cache_backend: CacheBackend = field(default=CacheBackend.FILE)
    storage_backend: StorageBackend = field(default=StorageBackend.LOCAL)

    # GCS configuration
    gcs_bucket: Optional[str] = field(default=None)
    gcs_prefix: str = field(default="uploads")

    # Firestore configuration
    firestore_collection: str = field(default="cache")

    # Redis configuration (optional)
    redis_host: Optional[str] = field(default=None)
    redis_port: int = field(default=6379)

    # Logging
    log_level: str = field(default="INFO")

    # Cache configuration
    cache_ttl_seconds: int = field(default=86400)  # 24 hours

    def __post_init__(self):
        """Auto-detect environment and configure backends."""
        self._detect_environment()
        self._configure_backends()
        self._setup_logging()

    def _detect_environment(self):
        """Detect if running in GCP and which environment."""
        # Check for GCP project ID
        self.gcp_project = os.getenv("GCP_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT")

        if self.gcp_project:
            # Running in GCP - check for production vs staging
            env_name = os.getenv("ENVIRONMENT", "staging").lower()
            if env_name == "production" or env_name == "prod":
                self.environment = Environment.GCP_PRODUCTION
            else:
                self.environment = Environment.GCP_STAGING
            logger.info(f"Detected GCP environment: {self.environment.value}")
        else:
            self.environment = Environment.LOCAL
            logger.info("Detected local development environment")

    def _configure_backends(self):
        """Configure backends based on environment and env vars."""
        # Cache backend
        cache_env = os.getenv("CACHE_BACKEND", "").lower()
        if cache_env == "firestore":
            self.cache_backend = CacheBackend.FIRESTORE
        elif cache_env == "redis":
            self.cache_backend = CacheBackend.REDIS
        elif cache_env == "memory":
            self.cache_backend = CacheBackend.MEMORY
        elif self.environment != Environment.LOCAL:
            # Default to Firestore in GCP
            self.cache_backend = CacheBackend.FIRESTORE
        else:
            self.cache_backend = CacheBackend.FILE

        # Storage backend
        storage_env = os.getenv("STORAGE_BACKEND", "").lower()
        if storage_env == "gcs":
            self.storage_backend = StorageBackend.GCS
        elif self.environment != Environment.LOCAL:
            # Default to GCS in GCP
            self.storage_backend = StorageBackend.GCS
        else:
            self.storage_backend = StorageBackend.LOCAL

        # GCS bucket
        self.gcs_bucket = os.getenv("GCS_BUCKET")
        if not self.gcs_bucket and self.gcp_project:
            self.gcs_bucket = f"{self.gcp_project}-hvac-uploads"

        # Redis configuration
        self.redis_host = os.getenv("REDIS_HOST")
        redis_port = os.getenv("REDIS_PORT")
        if redis_port:
            self.redis_port = int(redis_port)

        # Log level
        self.log_level = os.getenv("LOG_LEVEL", "INFO").upper()

        # Cache TTL
        cache_ttl = os.getenv("CACHE_TTL_SECONDS")
        if cache_ttl:
            self.cache_ttl_seconds = int(cache_ttl)

        logger.info(f"Cache backend: {self.cache_backend.value}")
        logger.info(f"Storage backend: {self.storage_backend.value}")

    def _setup_logging(self):
        """Configure logging based on environment."""
        logging.basicConfig(
            level=getattr(logging, self.log_level, logging.INFO),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # In GCP, use structured logging for Cloud Logging
        if self.environment != Environment.LOCAL:
            try:
                import google.cloud.logging
                client = google.cloud.logging.Client()
                client.setup_logging()
                logger.info("Cloud Logging configured")
            except ImportError:
                logger.warning("google-cloud-logging not installed, using standard logging")
            except Exception as e:
                logger.warning(f"Could not configure Cloud Logging: {e}")

    def is_gcp(self) -> bool:
        """Check if running in GCP."""
        return self.environment != Environment.LOCAL

    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == Environment.GCP_PRODUCTION

    def get_anthropic_api_key(self) -> Optional[str]:
        """
        Get Anthropic API key.

        In local environment, uses ANTHROPIC_API_KEY env var.
        In GCP, fetches from Secret Manager.
        """
        # First check environment variable
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            return api_key

        # In GCP, try Secret Manager
        if self.is_gcp():
            try:
                from secrets_manager import get_secret
                return get_secret("anthropic-api-key", project_id=self.gcp_project)
            except Exception as e:
                logger.error(f"Failed to get Anthropic API key from Secret Manager: {e}")

        return None

    def get_gemini_api_key(self) -> Optional[str]:
        """
        Get Gemini API key.

        In local environment, uses GEMINI_API_KEY env var.
        In GCP, fetches from Secret Manager.
        """
        # First check environment variable
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            return api_key

        # In GCP, try Secret Manager
        if self.is_gcp():
            try:
                from secrets_manager import get_secret
                return get_secret("gemini-api-key", project_id=self.gcp_project)
            except Exception as e:
                logger.error(f"Failed to get Gemini API key from Secret Manager: {e}")

        return None

    def get_cache(self):
        """
        Get configured cache instance.

        Returns appropriate cache backend based on configuration.
        """
        if self.cache_backend == CacheBackend.FILE:
            from utils_cache import FileCache
            return FileCache()
        elif self.cache_backend == CacheBackend.FIRESTORE:
            from firestore_cache import FirestoreCache
            return FirestoreCache(
                project_id=self.gcp_project,
                collection=self.firestore_collection,
                default_ttl=self.cache_ttl_seconds
            )
        elif self.cache_backend == CacheBackend.REDIS:
            from firestore_cache import RedisCache
            return RedisCache(
                host=self.redis_host,
                port=self.redis_port,
                default_ttl=self.cache_ttl_seconds
            )
        elif self.cache_backend == CacheBackend.MEMORY:
            from firestore_cache import MemoryCache
            return MemoryCache(default_ttl=self.cache_ttl_seconds)
        else:
            raise ValueError(f"Unknown cache backend: {self.cache_backend}")

    def get_storage(self):
        """
        Get configured storage instance.

        Returns appropriate storage backend based on configuration.
        """
        if self.storage_backend == StorageBackend.LOCAL:
            from gcs_storage import LocalStorage
            return LocalStorage()
        elif self.storage_backend == StorageBackend.GCS:
            from gcs_storage import GCSStorage
            if not self.gcs_bucket:
                raise ValueError("GCS_BUCKET environment variable required for GCS storage")
            return GCSStorage(
                bucket_name=self.gcs_bucket,
                prefix=self.gcs_prefix
            )
        else:
            raise ValueError(f"Unknown storage backend: {self.storage_backend}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for logging/debugging."""
        return {
            "environment": self.environment.value,
            "gcp_project": self.gcp_project,
            "cache_backend": self.cache_backend.value,
            "storage_backend": self.storage_backend.value,
            "gcs_bucket": self.gcs_bucket,
            "log_level": self.log_level,
            "cache_ttl_seconds": self.cache_ttl_seconds,
        }


# Global configuration instance (singleton)
_config: Optional[CloudConfig] = None


def get_config() -> CloudConfig:
    """Get global configuration instance."""
    global _config
    if _config is None:
        _config = CloudConfig()
    return _config


# Convenience aliases
config = get_config()


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    # Print current configuration
    cfg = get_config()
    print("Current Configuration:")
    print("-" * 40)
    for key, value in cfg.to_dict().items():
        print(f"  {key}: {value}")
    print("-" * 40)

    # Test API key retrieval
    anthropic_key = cfg.get_anthropic_api_key()
    print(f"Anthropic API Key: {'***' + anthropic_key[-4:] if anthropic_key else 'Not configured'}")

    gemini_key = cfg.get_gemini_api_key()
    print(f"Gemini API Key: {'***' + gemini_key[-4:] if gemini_key else 'Not configured'}")
