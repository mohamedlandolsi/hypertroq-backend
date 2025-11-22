"""
Google Cloud Storage utility functions.

Provides file upload, download, deletion, and signed URL generation
for Google Cloud Storage buckets.
"""

import logging
from datetime import timedelta
from typing import Optional

from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError, NotFound

from app.core.config import settings

logger = logging.getLogger(__name__)


class CloudStorageClient:
    """
    Google Cloud Storage client for file operations.
    
    Handles file uploads, deletions, and signed URL generation
    for secure access to private files.
    """

    def __init__(self) -> None:
        """Initialize Google Cloud Storage client."""
        try:
            self.client = storage.Client(project=settings.GOOGLE_CLOUD_PROJECT)
            logger.info(
                f"Google Cloud Storage client initialized for project: {settings.GOOGLE_CLOUD_PROJECT}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Google Cloud Storage client: {e}")
            self.client = None

    def _get_bucket(self, bucket_name: str) -> Optional[storage.Bucket]:
        """
        Get bucket instance.
        
        Args:
            bucket_name: Name of the GCS bucket
            
        Returns:
            Bucket instance or None if error
        """
        if not self.client:
            logger.error("Storage client not initialized")
            return None

        try:
            return self.client.bucket(bucket_name)
        except Exception as e:
            logger.error(f"Failed to get bucket {bucket_name}: {e}")
            return None

    async def upload_file(
        self,
        file_content: bytes,
        bucket_name: str,
        file_path: str,
        content_type: Optional[str] = None,
        make_public: bool = False,
    ) -> Optional[str]:
        """
        Upload file to Google Cloud Storage.
        
        Args:
            file_content: File content as bytes
            bucket_name: GCS bucket name
            file_path: Destination path in bucket (e.g., 'users/profile/image.jpg')
            content_type: MIME type (e.g., 'image/jpeg')
            make_public: Whether to make file publicly accessible
            
        Returns:
            Public URL if make_public=True, otherwise None
            
        Raises:
            GoogleCloudError: If upload fails
            
        Example:
            url = await storage_client.upload_file(
                file_content=image_bytes,
                bucket_name='hypertroq-user-uploads',
                file_path='users/123/profile.jpg',
                content_type='image/jpeg',
                make_public=True
            )
        """
        try:
            bucket = self._get_bucket(bucket_name)
            if not bucket:
                raise GoogleCloudError("Bucket not accessible")

            blob = bucket.blob(file_path)
            
            # Set content type if provided
            if content_type:
                blob.content_type = content_type

            # Upload file
            blob.upload_from_string(file_content)
            
            # Make public if requested
            if make_public:
                blob.make_public()
                public_url = blob.public_url
                logger.info(f"File uploaded and made public: {file_path}")
                return public_url
            
            logger.info(f"File uploaded: {file_path}")
            return None

        except GoogleCloudError as e:
            logger.error(f"Failed to upload file {file_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error uploading file {file_path}: {e}")
            raise GoogleCloudError(f"Upload failed: {str(e)}")

    async def delete_file(self, bucket_name: str, file_path: str) -> bool:
        """
        Delete file from Google Cloud Storage.
        
        Args:
            bucket_name: GCS bucket name
            file_path: Path to file in bucket
            
        Returns:
            True if deleted successfully, False otherwise
            
        Example:
            success = await storage_client.delete_file(
                bucket_name='hypertroq-user-uploads',
                file_path='users/123/old-profile.jpg'
            )
        """
        try:
            bucket = self._get_bucket(bucket_name)
            if not bucket:
                return False

            blob = bucket.blob(file_path)
            
            # Check if file exists
            if not blob.exists():
                logger.warning(f"File not found: {file_path}")
                return False

            # Delete file
            blob.delete()
            logger.info(f"File deleted: {file_path}")
            return True

        except NotFound:
            logger.warning(f"File not found: {file_path}")
            return False
        except GoogleCloudError as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting file {file_path}: {e}")
            return False

    async def generate_signed_url(
        self,
        bucket_name: str,
        file_path: str,
        expiration_minutes: int = 60,
        method: str = "GET",
    ) -> Optional[str]:
        """
        Generate signed URL for temporary file access.
        
        Args:
            bucket_name: GCS bucket name
            file_path: Path to file in bucket
            expiration_minutes: URL expiration time in minutes (default: 60)
            method: HTTP method ('GET', 'PUT', 'DELETE')
            
        Returns:
            Signed URL string or None if error
            
        Example:
            # Generate download URL (valid for 1 hour)
            url = await storage_client.generate_signed_url(
                bucket_name='hypertroq-exports',
                file_path='reports/user-123-data.csv',
                expiration_minutes=60
            )
            
            # Generate upload URL (valid for 15 minutes)
            url = await storage_client.generate_signed_url(
                bucket_name='hypertroq-user-uploads',
                file_path='users/123/new-file.pdf',
                expiration_minutes=15,
                method='PUT'
            )
        """
        try:
            bucket = self._get_bucket(bucket_name)
            if not bucket:
                return None

            blob = bucket.blob(file_path)
            
            # Generate signed URL
            url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(minutes=expiration_minutes),
                method=method,
            )
            
            logger.info(
                f"Signed URL generated for {file_path} (expires in {expiration_minutes} min)"
            )
            return url

        except GoogleCloudError as e:
            logger.error(f"Failed to generate signed URL for {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(
                f"Unexpected error generating signed URL for {file_path}: {e}"
            )
            return None

    async def file_exists(self, bucket_name: str, file_path: str) -> bool:
        """
        Check if file exists in bucket.
        
        Args:
            bucket_name: GCS bucket name
            file_path: Path to file in bucket
            
        Returns:
            True if file exists, False otherwise
        """
        try:
            bucket = self._get_bucket(bucket_name)
            if not bucket:
                return False

            blob = bucket.blob(file_path)
            return blob.exists()

        except Exception as e:
            logger.error(f"Error checking file existence {file_path}: {e}")
            return False

    async def get_file_metadata(
        self, bucket_name: str, file_path: str
    ) -> Optional[dict]:
        """
        Get file metadata.
        
        Args:
            bucket_name: GCS bucket name
            file_path: Path to file in bucket
            
        Returns:
            Dictionary with file metadata or None if error
        """
        try:
            bucket = self._get_bucket(bucket_name)
            if not bucket:
                return None

            blob = bucket.blob(file_path)
            
            if not blob.exists():
                return None

            blob.reload()
            
            return {
                "name": blob.name,
                "size": blob.size,
                "content_type": blob.content_type,
                "created": blob.time_created,
                "updated": blob.updated,
                "md5_hash": blob.md5_hash,
                "public_url": blob.public_url if blob.public_url else None,
            }

        except Exception as e:
            logger.error(f"Error getting file metadata {file_path}: {e}")
            return None


# Global storage client instance
storage_client = CloudStorageClient()


# Convenience functions for common operations
async def upload_profile_image(
    user_id: str, image_content: bytes, extension: str = "jpg"
) -> Optional[str]:
    """
    Upload user profile image.
    
    Args:
        user_id: User UUID
        image_content: Image bytes
        extension: File extension (jpg, png, etc.)
        
    Returns:
        Public URL of uploaded image
    """
    file_path = f"users/{user_id}/profile.{extension}"
    content_type = f"image/{extension}"
    
    return await storage_client.upload_file(
        file_content=image_content,
        bucket_name=settings.GOOGLE_CLOUD_STORAGE_BUCKET,
        file_path=file_path,
        content_type=content_type,
        make_public=True,
    )


async def delete_profile_image(user_id: str, extension: str = "jpg") -> bool:
    """
    Delete user profile image.
    
    Args:
        user_id: User UUID
        extension: File extension
        
    Returns:
        True if deleted successfully
    """
    file_path = f"users/{user_id}/profile.{extension}"
    
    return await storage_client.delete_file(
        bucket_name=settings.GOOGLE_CLOUD_STORAGE_BUCKET,
        file_path=file_path,
    )


async def upload_exercise_media(
    exercise_id: str,
    media_content: bytes,
    media_type: str = "image",
    extension: str = "jpg",
) -> Optional[str]:
    """
    Upload exercise image or video.
    
    Args:
        exercise_id: Exercise UUID
        media_content: Media bytes
        media_type: 'image' or 'video'
        extension: File extension
        
    Returns:
        Public URL of uploaded media
    """
    file_path = f"exercises/{exercise_id}/{media_type}.{extension}"
    content_type = f"{media_type}/{extension}"
    
    return await storage_client.upload_file(
        file_content=media_content,
        bucket_name=settings.GOOGLE_CLOUD_STORAGE_BUCKET,
        file_path=file_path,
        content_type=content_type,
        make_public=True,
    )
