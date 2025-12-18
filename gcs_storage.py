"""
Google Cloud Storage Integration Module
========================================

Provides abstracted file storage operations for both local
development and Google Cloud Storage (GCS) deployment.

Supports:
- PDF upload and retrieval
- Quote/report file storage
- Signed URL generation for downloads
- Automatic cleanup via lifecycle policies

Usage:
    from gcs_storage import get_storage

    storage = get_storage()

    # Upload a file
    url = storage.upload_file(file_bytes, "project-123/spec.pdf")

    # Get download URL
    download_url = storage.get_download_url("project-123/spec.pdf")

    # Delete a file
    storage.delete_file("project-123/spec.pdf")
"""

import os
import io
import uuid
import hashlib
import tempfile
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, BinaryIO, Union, List, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class StorageBackend(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    def upload_file(
        self,
        file_data: Union[bytes, BinaryIO],
        destination_path: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Upload a file to storage.

        Args:
            file_data: File contents as bytes or file-like object
            destination_path: Path within storage (e.g., "uploads/project-123/spec.pdf")
            content_type: MIME type (auto-detected if not provided)
            metadata: Optional metadata to attach to the file

        Returns:
            URL or path to access the uploaded file
        """
        pass

    @abstractmethod
    def download_file(self, source_path: str) -> bytes:
        """
        Download a file from storage.

        Args:
            source_path: Path to the file in storage

        Returns:
            File contents as bytes
        """
        pass

    @abstractmethod
    def get_download_url(
        self,
        source_path: str,
        expiration_minutes: int = 60
    ) -> str:
        """
        Get a URL to download a file.

        Args:
            source_path: Path to the file in storage
            expiration_minutes: How long the URL should be valid

        Returns:
            Download URL (signed URL for GCS, file path for local)
        """
        pass

    @abstractmethod
    def delete_file(self, source_path: str) -> bool:
        """
        Delete a file from storage.

        Args:
            source_path: Path to the file in storage

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    def list_files(self, prefix: str = "") -> List[str]:
        """
        List files in storage.

        Args:
            prefix: Path prefix to filter by

        Returns:
            List of file paths
        """
        pass

    @abstractmethod
    def file_exists(self, source_path: str) -> bool:
        """
        Check if a file exists.

        Args:
            source_path: Path to the file in storage

        Returns:
            True if exists, False otherwise
        """
        pass


class LocalStorage(StorageBackend):
    """
    Local filesystem storage backend.

    Used for local development. Files are stored in a configurable
    directory (defaults to ./storage).
    """

    def __init__(self, base_dir: str = "./storage"):
        """
        Initialize local storage.

        Args:
            base_dir: Base directory for file storage
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"LocalStorage initialized at {self.base_dir}")

    def _get_full_path(self, path: str) -> Path:
        """Get full filesystem path."""
        return self.base_dir / path

    def upload_file(
        self,
        file_data: Union[bytes, BinaryIO],
        destination_path: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """Upload file to local filesystem."""
        full_path = self._get_full_path(destination_path)

        # Create parent directories
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # Handle bytes vs file-like object
        if isinstance(file_data, bytes):
            data = file_data
        else:
            data = file_data.read()

        # Write file
        with open(full_path, 'wb') as f:
            f.write(data)

        # Store metadata in sidecar file (optional)
        if metadata:
            meta_path = full_path.with_suffix(full_path.suffix + '.meta')
            import json
            with open(meta_path, 'w') as f:
                json.dump({
                    "content_type": content_type,
                    "metadata": metadata,
                    "uploaded_at": datetime.now().isoformat()
                }, f)

        logger.info(f"Uploaded {len(data)} bytes to {full_path}")
        return str(full_path)

    def download_file(self, source_path: str) -> bytes:
        """Download file from local filesystem."""
        full_path = self._get_full_path(source_path)

        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {source_path}")

        with open(full_path, 'rb') as f:
            return f.read()

    def get_download_url(
        self,
        source_path: str,
        expiration_minutes: int = 60
    ) -> str:
        """Get local file path (URL not applicable for local storage)."""
        full_path = self._get_full_path(source_path)

        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {source_path}")

        return str(full_path)

    def delete_file(self, source_path: str) -> bool:
        """Delete file from local filesystem."""
        full_path = self._get_full_path(source_path)

        if full_path.exists():
            full_path.unlink()

            # Also delete metadata file if exists
            meta_path = full_path.with_suffix(full_path.suffix + '.meta')
            if meta_path.exists():
                meta_path.unlink()

            logger.info(f"Deleted {full_path}")
            return True

        return False

    def list_files(self, prefix: str = "") -> List[str]:
        """List files in local storage."""
        search_dir = self._get_full_path(prefix) if prefix else self.base_dir
        files = []

        if search_dir.exists():
            for file_path in search_dir.rglob("*"):
                if file_path.is_file() and not file_path.suffix == '.meta':
                    relative_path = file_path.relative_to(self.base_dir)
                    files.append(str(relative_path))

        return files

    def file_exists(self, source_path: str) -> bool:
        """Check if file exists in local storage."""
        return self._get_full_path(source_path).exists()


class GCSStorage(StorageBackend):
    """
    Google Cloud Storage backend.

    Used for GCP deployments. Provides:
    - Secure file storage
    - Signed URLs for downloads
    - Automatic cleanup via lifecycle policies
    - IAM-based access control
    """

    def __init__(
        self,
        bucket_name: str,
        prefix: str = "",
        project_id: Optional[str] = None
    ):
        """
        Initialize GCS storage.

        Args:
            bucket_name: GCS bucket name
            prefix: Optional prefix for all paths (e.g., "uploads")
            project_id: GCP project ID (auto-detected if not provided)
        """
        try:
            from google.cloud import storage
        except ImportError:
            raise ImportError(
                "google-cloud-storage is required for GCS backend. "
                "Install with: pip install google-cloud-storage"
            )

        self.bucket_name = bucket_name
        self.prefix = prefix.strip("/")
        self.project_id = project_id or os.getenv("GCP_PROJECT")

        # Initialize client
        self.client = storage.Client(project=self.project_id)
        self.bucket = self.client.bucket(bucket_name)

        logger.info(f"GCSStorage initialized for gs://{bucket_name}/{prefix}")

    def _get_full_path(self, path: str) -> str:
        """Get full GCS object path including prefix."""
        if self.prefix:
            return f"{self.prefix}/{path.lstrip('/')}"
        return path.lstrip('/')

    def _detect_content_type(self, path: str) -> str:
        """Detect content type from file extension."""
        import mimetypes
        content_type, _ = mimetypes.guess_type(path)
        return content_type or 'application/octet-stream'

    def upload_file(
        self,
        file_data: Union[bytes, BinaryIO],
        destination_path: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """Upload file to GCS."""
        from google.cloud import storage

        full_path = self._get_full_path(destination_path)
        blob = self.bucket.blob(full_path)

        # Set content type
        if content_type:
            blob.content_type = content_type
        else:
            blob.content_type = self._detect_content_type(destination_path)

        # Set metadata
        if metadata:
            blob.metadata = metadata

        # Handle bytes vs file-like object
        if isinstance(file_data, bytes):
            blob.upload_from_string(file_data, content_type=blob.content_type)
            size = len(file_data)
        else:
            blob.upload_from_file(file_data, content_type=blob.content_type)
            size = file_data.seek(0, 2)  # Get file size
            file_data.seek(0)

        logger.info(f"Uploaded {size} bytes to gs://{self.bucket_name}/{full_path}")
        return f"gs://{self.bucket_name}/{full_path}"

    def download_file(self, source_path: str) -> bytes:
        """Download file from GCS."""
        full_path = self._get_full_path(source_path)
        blob = self.bucket.blob(full_path)

        if not blob.exists():
            raise FileNotFoundError(f"File not found: gs://{self.bucket_name}/{full_path}")

        return blob.download_as_bytes()

    def get_download_url(
        self,
        source_path: str,
        expiration_minutes: int = 60
    ) -> str:
        """Generate signed URL for file download."""
        full_path = self._get_full_path(source_path)
        blob = self.bucket.blob(full_path)

        if not blob.exists():
            raise FileNotFoundError(f"File not found: gs://{self.bucket_name}/{full_path}")

        # Generate signed URL
        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=expiration_minutes),
            method="GET"
        )

        logger.debug(f"Generated signed URL for {full_path}, expires in {expiration_minutes}m")
        return url

    def delete_file(self, source_path: str) -> bool:
        """Delete file from GCS."""
        full_path = self._get_full_path(source_path)
        blob = self.bucket.blob(full_path)

        if blob.exists():
            blob.delete()
            logger.info(f"Deleted gs://{self.bucket_name}/{full_path}")
            return True

        return False

    def list_files(self, prefix: str = "") -> List[str]:
        """List files in GCS bucket."""
        search_prefix = self._get_full_path(prefix) if prefix else self.prefix
        blobs = self.client.list_blobs(self.bucket, prefix=search_prefix)

        files = []
        for blob in blobs:
            # Remove prefix from path
            if self.prefix and blob.name.startswith(self.prefix + "/"):
                relative_path = blob.name[len(self.prefix) + 1:]
            else:
                relative_path = blob.name
            files.append(relative_path)

        return files

    def file_exists(self, source_path: str) -> bool:
        """Check if file exists in GCS."""
        full_path = self._get_full_path(source_path)
        blob = self.bucket.blob(full_path)
        return blob.exists()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def generate_unique_path(
    filename: str,
    session_id: Optional[str] = None,
    category: str = "uploads"
) -> str:
    """
    Generate a unique storage path for a file.

    Args:
        filename: Original filename
        session_id: Optional session ID for grouping
        category: File category (uploads, quotes, etc.)

    Returns:
        Unique path like "uploads/2024-01/session-123/abc12345-spec.pdf"
    """
    # Generate unique ID
    unique_id = uuid.uuid4().hex[:8]

    # Clean filename
    safe_filename = "".join(c for c in filename if c.isalnum() or c in ".-_")

    # Date-based prefix for organization
    date_prefix = datetime.now().strftime("%Y-%m")

    # Build path
    if session_id:
        return f"{category}/{date_prefix}/{session_id}/{unique_id}-{safe_filename}"
    else:
        return f"{category}/{date_prefix}/{unique_id}-{safe_filename}"


def get_file_hash(file_data: Union[bytes, BinaryIO]) -> str:
    """
    Calculate SHA-256 hash of file contents.

    Args:
        file_data: File contents

    Returns:
        Hex digest of hash
    """
    hasher = hashlib.sha256()

    if isinstance(file_data, bytes):
        hasher.update(file_data)
    else:
        # Read in chunks for large files
        pos = file_data.tell()
        while chunk := file_data.read(8192):
            hasher.update(chunk)
        file_data.seek(pos)  # Reset position

    return hasher.hexdigest()


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

_storage: Optional[StorageBackend] = None


def get_storage() -> StorageBackend:
    """
    Get configured storage backend.

    Returns LocalStorage for local development,
    GCSStorage for GCP deployments.
    """
    global _storage

    if _storage is None:
        storage_backend = os.getenv("STORAGE_BACKEND", "local").lower()

        if storage_backend == "gcs":
            bucket_name = os.getenv("GCS_BUCKET")
            if not bucket_name:
                raise ValueError("GCS_BUCKET environment variable required for GCS storage")
            _storage = GCSStorage(bucket_name=bucket_name)
        else:
            _storage = LocalStorage()

    return _storage


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)

    # Use local storage for demo
    storage = LocalStorage("./test_storage")

    # Test upload
    test_data = b"Hello, World! This is a test PDF file."
    path = generate_unique_path("test.pdf", session_id="demo-123")
    url = storage.upload_file(test_data, path, content_type="application/pdf")
    print(f"Uploaded to: {url}")

    # Test download
    downloaded = storage.download_file(path)
    print(f"Downloaded {len(downloaded)} bytes")

    # Test list
    files = storage.list_files()
    print(f"Files in storage: {files}")

    # Test exists
    exists = storage.file_exists(path)
    print(f"File exists: {exists}")

    # Test delete
    deleted = storage.delete_file(path)
    print(f"Deleted: {deleted}")

    # Cleanup
    import shutil
    shutil.rmtree("./test_storage", ignore_errors=True)
    print("Cleanup complete")
