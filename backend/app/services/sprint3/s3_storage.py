"""S3 Storage service for assets and exports"""
import asyncio
import logging
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from pathlib import Path
from typing import Optional, Dict, Any, List
import mimetypes
from datetime import datetime, timedelta

from ...core.config import settings

logger = logging.getLogger(__name__)

class S3StorageManager:
    """S3 storage management service"""
    
    def __init__(self):
        self.bucket_name = settings.S3_BUCKET
        self.region = settings.AWS_REGION
        
        # Initialize S3 client
        try:
            if settings.S3_ENDPOINT_URL:
                # For MinIO or other S3-compatible services
                self.s3_client = boto3.client(
                    's3',
                    endpoint_url=settings.S3_ENDPOINT_URL,
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=self.region
                )
            else:
                # For AWS S3
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=self.region
                )
            
            logger.info("S3 client initialized successfully")
            
        except NoCredentialsError:
            logger.warning("AWS credentials not found, S3 storage disabled")
            self.s3_client = None
        except Exception as e:
            logger.error(f"Error initializing S3 client: {e}")
            self.s3_client = None
    
    async def upload_file(self, file_path: Path, s3_key: str, content_type: Optional[str] = None) -> bool:
        """Upload file to S3"""
        if not self.s3_client or not self.bucket_name:
            logger.warning("S3 not configured, skipping upload")
            return False
        
        try:
            if not file_path.exists():
                logger.error(f"File not found: {file_path}")
                return False
            
            # Determine content type
            if not content_type:
                content_type, _ = mimetypes.guess_type(str(file_path))
                if not content_type:
                    content_type = 'application/octet-stream'
            
            # Upload file
            self.s3_client.upload_file(
                str(file_path),
                self.bucket_name,
                s3_key,
                ExtraArgs={'ContentType': content_type}
            )
            
            logger.info(f"File uploaded to S3: {s3_key}")
            return True
            
        except ClientError as e:
            logger.error(f"Error uploading file to S3: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error uploading file: {e}")
            return False
    
    async def download_file(self, s3_key: str, local_path: Path) -> bool:
        """Download file from S3"""
        if not self.s3_client or not self.bucket_name:
            logger.warning("S3 not configured, skipping download")
            return False
        
        try:
            # Ensure local directory exists
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Download file
            self.s3_client.download_file(
                self.bucket_name,
                s3_key,
                str(local_path)
            )
            
            logger.info(f"File downloaded from S3: {s3_key}")
            return True
            
        except ClientError as e:
            logger.error(f"Error downloading file from S3: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error downloading file: {e}")
            return False
    
    async def generate_presigned_url(self, s3_key: str, expiration: int = 3600) -> Optional[str]:
        """Generate presigned URL for file access"""
        if not self.s3_client or not self.bucket_name:
            logger.warning("S3 not configured, cannot generate presigned URL")
            return None
        
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expiration
            )
            
            logger.info(f"Generated presigned URL for: {s3_key}")
            return url
            
        except ClientError as e:
            logger.error(f"Error generating presigned URL: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error generating presigned URL: {e}")
            return None
    
    async def delete_file(self, s3_key: str) -> bool:
        """Delete file from S3"""
        if not self.s3_client or not self.bucket_name:
            logger.warning("S3 not configured, skipping delete")
            return False
        
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            logger.info(f"File deleted from S3: {s3_key}")
            return True
            
        except ClientError as e:
            logger.error(f"Error deleting file from S3: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting file: {e}")
            return False
    
    async def list_files(self, prefix: str = "") -> List[Dict[str, Any]]:
        """List files in S3 bucket with given prefix"""
        if not self.s3_client or not self.bucket_name:
            logger.warning("S3 not configured, cannot list files")
            return []
        
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            files = []
            for obj in response.get('Contents', []):
                files.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'],
                    'etag': obj['ETag']
                })
            
            logger.info(f"Listed {len(files)} files with prefix: {prefix}")
            return files
            
        except ClientError as e:
            logger.error(f"Error listing files from S3: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error listing files: {e}")
            return []
    
    async def get_file_info(self, s3_key: str) -> Optional[Dict[str, Any]]:
        """Get file information from S3"""
        if not self.s3_client or not self.bucket_name:
            logger.warning("S3 not configured, cannot get file info")
            return None
        
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            return {
                'key': s3_key,
                'size': response['ContentLength'],
                'content_type': response.get('ContentType', 'application/octet-stream'),
                'last_modified': response['LastModified'],
                'etag': response['ETag']
            }
            
        except ClientError as e:
            logger.error(f"Error getting file info from S3: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting file info: {e}")
            return None
    
    async def cleanup_old_files(self, prefix: str, max_age_days: int = 7) -> int:
        """Clean up old files in S3"""
        if not self.s3_client or not self.bucket_name:
            logger.warning("S3 not configured, skipping cleanup")
            return 0
        
        try:
            files = await self.list_files(prefix)
            cutoff_date = datetime.now() - timedelta(days=max_age_days)
            
            deleted_count = 0
            for file_info in files:
                if file_info['last_modified'].replace(tzinfo=None) < cutoff_date:
                    if await self.delete_file(file_info['key']):
                        deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} old files from S3")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old files: {e}")
            return 0
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get S3 storage statistics"""
        if not self.s3_client or not self.bucket_name:
            return {"enabled": False, "message": "S3 not configured"}
        
        try:
            # Get bucket size and file count
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name)
            
            total_size = 0
            file_count = 0
            
            for obj in response.get('Contents', []):
                total_size += obj['Size']
                file_count += 1
            
            return {
                "enabled": True,
                "bucket": self.bucket_name,
                "region": self.region,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "file_count": file_count
            }
            
        except ClientError as e:
            logger.error(f"Error getting S3 storage stats: {e}")
            return {"enabled": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error getting storage stats: {e}")
            return {"enabled": False, "error": str(e)}