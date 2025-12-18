"""
Google Secret Manager Integration
==================================

Secure API key and credential management using Google Secret Manager.
Falls back to environment variables for local development.

Usage:
    from secrets_manager import get_secret, SecretManager

    # Simple function call
    api_key = get_secret("anthropic-api-key")

    # Using manager class
    manager = SecretManager(project_id="my-project")
    api_key = manager.get_secret("anthropic-api-key")
"""

import os
import logging
from typing import Optional, Dict
from functools import lru_cache

logger = logging.getLogger(__name__)


class SecretManager:
    """
    Wrapper for Google Secret Manager.

    Provides secure secret access with:
    - Automatic fallback to environment variables
    - Caching for performance
    - Version support
    - Rotation handling
    """

    def __init__(self, project_id: Optional[str] = None):
        """
        Initialize Secret Manager.

        Args:
            project_id: GCP project ID (auto-detected if not provided)
        """
        self.project_id = project_id or os.getenv("GCP_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT")
        self._client = None
        self._cache: Dict[str, str] = {}

    @property
    def client(self):
        """Lazy initialization of Secret Manager client."""
        if self._client is None:
            try:
                from google.cloud import secretmanager
                self._client = secretmanager.SecretManagerServiceClient()
                logger.info("Secret Manager client initialized")
            except ImportError:
                logger.warning(
                    "google-cloud-secret-manager not installed. "
                    "Falling back to environment variables."
                )
                self._client = False  # Mark as unavailable
            except Exception as e:
                logger.warning(f"Failed to initialize Secret Manager: {e}")
                self._client = False

        return self._client if self._client else None

    def get_secret(
        self,
        secret_id: str,
        version: str = "latest",
        use_cache: bool = True
    ) -> Optional[str]:
        """
        Get a secret value.

        First checks environment variables (for local dev),
        then tries Secret Manager (for GCP deployment).

        Args:
            secret_id: Secret ID (e.g., "anthropic-api-key")
            version: Secret version (default: "latest")
            use_cache: Whether to cache the result

        Returns:
            Secret value or None if not found
        """
        # Check cache first
        cache_key = f"{secret_id}:{version}"
        if use_cache and cache_key in self._cache:
            logger.debug(f"Using cached secret: {secret_id}")
            return self._cache[cache_key]

        # Try environment variable first (local development)
        env_key = secret_id.upper().replace("-", "_")
        env_value = os.getenv(env_key)
        if env_value:
            logger.debug(f"Using environment variable: {env_key}")
            if use_cache:
                self._cache[cache_key] = env_value
            return env_value

        # Try Secret Manager
        if self.client and self.project_id:
            try:
                secret_name = f"projects/{self.project_id}/secrets/{secret_id}/versions/{version}"
                response = self.client.access_secret_version(request={"name": secret_name})
                value = response.payload.data.decode("UTF-8")

                logger.info(f"Retrieved secret from Secret Manager: {secret_id}")
                if use_cache:
                    self._cache[cache_key] = value
                return value

            except Exception as e:
                logger.warning(f"Failed to get secret '{secret_id}' from Secret Manager: {e}")

        logger.warning(f"Secret not found: {secret_id}")
        return None

    def invalidate_cache(self, secret_id: Optional[str] = None):
        """
        Invalidate cached secrets.

        Args:
            secret_id: Specific secret to invalidate, or None for all
        """
        if secret_id:
            # Remove specific secret from cache
            keys_to_remove = [k for k in self._cache if k.startswith(f"{secret_id}:")]
            for key in keys_to_remove:
                del self._cache[key]
        else:
            # Clear all
            self._cache.clear()

        logger.info(f"Cache invalidated: {secret_id or 'all'}")

    def secret_exists(self, secret_id: str) -> bool:
        """
        Check if a secret exists.

        Args:
            secret_id: Secret ID to check

        Returns:
            True if secret exists (in env vars or Secret Manager)
        """
        # Check environment variable
        env_key = secret_id.upper().replace("-", "_")
        if os.getenv(env_key):
            return True

        # Check Secret Manager
        if self.client and self.project_id:
            try:
                secret_name = f"projects/{self.project_id}/secrets/{secret_id}"
                self.client.get_secret(request={"name": secret_name})
                return True
            except Exception:
                pass

        return False

    def list_secrets(self) -> list:
        """
        List available secrets.

        Returns:
            List of secret IDs
        """
        secrets = []

        if self.client and self.project_id:
            try:
                parent = f"projects/{self.project_id}"
                for secret in self.client.list_secrets(request={"parent": parent}):
                    # Extract secret ID from full name
                    secret_id = secret.name.split("/")[-1]
                    secrets.append(secret_id)
            except Exception as e:
                logger.warning(f"Failed to list secrets: {e}")

        return secrets


# =============================================================================
# MODULE-LEVEL FUNCTIONS
# =============================================================================

# Global manager instance
_manager: Optional[SecretManager] = None


def get_manager(project_id: Optional[str] = None) -> SecretManager:
    """Get global SecretManager instance."""
    global _manager
    if _manager is None:
        _manager = SecretManager(project_id=project_id)
    return _manager


def get_secret(
    secret_id: str,
    version: str = "latest",
    project_id: Optional[str] = None
) -> Optional[str]:
    """
    Get a secret value.

    Convenience function that uses the global SecretManager instance.

    Args:
        secret_id: Secret ID (e.g., "anthropic-api-key")
        version: Secret version (default: "latest")
        project_id: Optional project ID override

    Returns:
        Secret value or None if not found

    Example:
        api_key = get_secret("anthropic-api-key")
    """
    manager = get_manager(project_id)
    return manager.get_secret(secret_id, version)


# =============================================================================
# COMMON SECRET ACCESSORS
# =============================================================================

@lru_cache(maxsize=1)
def get_anthropic_api_key() -> Optional[str]:
    """Get Anthropic API key from secrets or environment."""
    return get_secret("anthropic-api-key")


@lru_cache(maxsize=1)
def get_gemini_api_key() -> Optional[str]:
    """Get Gemini API key from secrets or environment."""
    return get_secret("gemini-api-key")


def clear_cached_secrets():
    """Clear all cached secrets (call after rotation)."""
    global _manager
    if _manager:
        _manager.invalidate_cache()

    # Also clear lru_cache for accessor functions
    get_anthropic_api_key.cache_clear()
    get_gemini_api_key.cache_clear()


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Test with environment variables
    os.environ["ANTHROPIC_API_KEY"] = "test-key-from-env"

    # Get secret (will use env var)
    key = get_secret("anthropic-api-key")
    print(f"Anthropic API Key: {key}")

    # Using the convenience function
    key2 = get_anthropic_api_key()
    print(f"Anthropic API Key (cached): {key2}")

    # Check if secret exists
    manager = get_manager()
    exists = manager.secret_exists("anthropic-api-key")
    print(f"Secret exists: {exists}")

    # Clear cache
    clear_cached_secrets()
    print("Cache cleared")
