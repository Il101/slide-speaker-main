"""
Google Cloud Storage Provider
"""
import asyncio
import logging
import os
from typing import Optional, Dict, Any, List
from pathlib import Path

try:
    from google.cloud import storage
    from google.api_core import exceptions as gcp_exceptions
    GOOGLE_STORAGE_AVAILABLE = True
except ImportError:
    GOOGLE_STORAGE_AVAILABLE = False
    logging.warning("Google Cloud Storage not available. Install google-cloud-storage")

logger = logging.getLogger(__name__)

class GoogleCloudStorageProvider:
    """Provider for Google Cloud Storage operations"""
    
    def __init__(self, bucket_name: str = None, base_url: str = None):
        self.bucket_name = bucket_name or os.getenv("GCS_BUCKET", "slide-speaker")
        self.base_url = base_url or os.getenv("GCS_BASE_URL", f"https://storage.googleapis.com/{self.bucket_name}")
        
        if not GOOGLE_STORAGE_AVAILABLE:
            logger.warning("Google Cloud Storage not available, will use local storage")
            self.use_local = True
        else:
            self.use_local = False
            # Initialize GCS client
            try:
                self.client = storage.Client()
                self.bucket = self.client.bucket(self.bucket_name)
            except Exception as e:
                logger.error(f"Failed to initialize Google Cloud Storage: {e}")
                self.use_local = True
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
    
    async def upload_bytes_async(self, data: bytes, remote_key: str) -> str:
        """
        Асинхронная загрузка файла для совместимости с тестами.
        
        Args:
            data: Данные для загрузки
            remote_key: Ключ для хранения
            
        Returns:
            str: URL загруженного файла
        """
        return self.upload_bytes(data, remote_key)
    
    async def download_file(self, remote_key: str) -> bytes:
        """
        Асинхронное скачивание файла для совместимости с тестами.
        
        Args:
            remote_key: Ключ файла
            
        Returns:
            bytes: Содержимое файла
        """
        try:
            if self.use_local:
                return self._download_bytes_local(remote_key)
            
            # Download from Google Cloud Storage
            blob = self.bucket.blob(remote_key)
            
            if not blob.exists():
                raise FileNotFoundError(f"File {remote_key} not found")
            
            return blob.download_as_bytes()
            
        except Exception as e:
            logger.error(f"Error downloading file from GCS: {e}")
            raise
    
    def upload_file(self, local_path: str, remote_key: str) -> str:
        """
        Загружает файл в GCS и возвращает публичный URL.
        
        Args:
            local_path: Локальный путь к файлу
            remote_key: Ключ для хранения в GCS
            
        Returns:
            Публичный URL файла (GCS_BASE_URL/remote_key)
        """
        try:
            if self.use_local:
                return self._upload_file_local(local_path, remote_key)
            
            # Upload to Google Cloud Storage
            blob = self.bucket.blob(remote_key)
            
            # Upload file
            blob.upload_from_filename(local_path)
            
            # Make blob publicly readable
            blob.make_public()
            
            # Return public URL
            public_url = f"{self.base_url}/{remote_key}"
            
            logger.info(f"Uploaded file to GCS: {local_path} -> {public_url}")
            return public_url
            
        except Exception as e:
            logger.error(f"Error uploading file to GCS: {e}")
            # Fallback to local storage
            logger.info("Falling back to local storage")
            return self._upload_file_local(local_path, remote_key)
    
    def upload_bytes(self, data: bytes, remote_key: str, content_type: str = None) -> str:
        """
        Загружает данные в GCS и возвращает публичный URL.
        
        Args:
            data: Данные для загрузки
            remote_key: Ключ для хранения в GCS
            content_type: MIME тип контента
            
        Returns:
            Публичный URL файла
        """
        try:
            if self.use_local:
                return self._upload_bytes_local(data, remote_key, content_type)
            
            # Upload to Google Cloud Storage
            blob = self.bucket.blob(remote_key)
            
            # Upload data
            blob.upload_from_string(data, content_type=content_type)
            
            # Make blob publicly readable
            blob.make_public()
            
            # Return public URL
            public_url = f"{self.base_url}/{remote_key}"
            
            logger.info(f"Uploaded bytes to GCS: {len(data)} bytes -> {public_url}")
            return public_url
            
        except Exception as e:
            logger.error(f"Error uploading bytes to GCS: {e}")
            # Fallback to local storage
            logger.info("Falling back to local storage")
            return self._upload_bytes_local(data, remote_key, content_type)
    
    def download_file(self, remote_key: str, local_path: str) -> bool:
        """
        Скачивает файл из GCS.
        
        Args:
            remote_key: Ключ файла в GCS
            local_path: Локальный путь для сохранения
            
        Returns:
            True если успешно, False если ошибка
        """
        try:
            if self.use_local:
                return self._download_file_local(remote_key, local_path)
            
            # Download from Google Cloud Storage
            blob = self.bucket.blob(remote_key)
            
            # Create local directory if needed
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Download file
            blob.download_to_filename(local_path)
            
            logger.info(f"Downloaded file from GCS: {remote_key} -> {local_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading file from GCS: {e}")
            return False
    
    def delete_file(self, remote_key: str) -> bool:
        """
        Удаляет файл из GCS.
        
        Args:
            remote_key: Ключ файла в GCS
            
        Returns:
            True если успешно, False если ошибка
        """
        try:
            if self.use_local:
                return self._delete_file_local(remote_key)
            
            # Delete from Google Cloud Storage
            blob = self.bucket.blob(remote_key)
            blob.delete()
            
            logger.info(f"Deleted file from GCS: {remote_key}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting file from GCS: {e}")
            return False
    
    def file_exists(self, remote_key: str) -> bool:
        """
        Проверяет существование файла в GCS.
        
        Args:
            remote_key: Ключ файла в GCS
            
        Returns:
            True если файл существует, False если нет
        """
        try:
            if self.use_local:
                return self._file_exists_local(remote_key)
            
            # Check existence in Google Cloud Storage
            blob = self.bucket.blob(remote_key)
            return blob.exists()
            
        except Exception as e:
            logger.error(f"Error checking file existence in GCS: {e}")
            return False
    
    def get_file_url(self, remote_key: str) -> str:
        """
        Получает публичный URL файла в GCS.
        
        Args:
            remote_key: Ключ файла в GCS
            
        Returns:
            Публичный URL файла
        """
        return f"{self.base_url}/{remote_key}"
    
    def list_files(self, prefix: str = "") -> List[str]:
        """
        Списывает файлы в GCS с заданным префиксом.
        
        Args:
            prefix: Префикс для фильтрации файлов
            
        Returns:
            Список ключей файлов
        """
        try:
            if self.use_local:
                return self._list_files_local(prefix)
            
            # List files in Google Cloud Storage
            blobs = self.bucket.list_blobs(prefix=prefix)
            return [blob.name for blob in blobs]
            
        except Exception as e:
            logger.error(f"Error listing files in GCS: {e}")
            return []
    
    def _upload_file_local(self, local_path: str, remote_key: str) -> str:
        """Fallback to local file system"""
        try:
            # Create local storage directory
            local_storage_dir = Path(".data/gcs_storage")
            local_storage_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy file to local storage
            local_file_path = local_storage_dir / remote_key
            local_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            import shutil
            shutil.copy2(local_path, local_file_path)
            
            # Return local URL
            local_url = f"/assets/gcs_storage/{remote_key}"
            
            logger.info(f"Uploaded file locally: {local_path} -> {local_url}")
            return local_url
            
        except Exception as e:
            logger.error(f"Error uploading file locally: {e}")
            raise
    
    def _upload_bytes_local(self, data: bytes, remote_key: str, content_type: str = None) -> str:
        """Fallback to local file system for bytes"""
        try:
            # Create local storage directory
            local_storage_dir = Path(".data/gcs_storage")
            local_storage_dir.mkdir(parents=True, exist_ok=True)
            
            # Save data to local file
            local_file_path = local_storage_dir / remote_key
            local_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(local_file_path, 'wb') as f:
                f.write(data)
            
            # Return local URL
            local_url = f"/assets/gcs_storage/{remote_key}"
            
            logger.info(f"Uploaded bytes locally: {len(data)} bytes -> {local_url}")
            return local_url
            
        except Exception as e:
            logger.error(f"Error uploading bytes locally: {e}")
            raise
    
    def _download_file_local(self, remote_key: str, local_path: str) -> bool:
        """Fallback to local file system"""
        try:
            # Get local file path
            local_storage_dir = Path(".data/gcs_storage")
            local_file_path = local_storage_dir / remote_key
            
            if not local_file_path.exists():
                return False
            
            # Copy file to destination
            import shutil
            shutil.copy2(local_file_path, local_path)
            
            logger.info(f"Downloaded file locally: {remote_key} -> {local_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading file locally: {e}")
            return False
    
    def _delete_file_local(self, remote_key: str) -> bool:
        """Fallback to local file system"""
        try:
            # Get local file path
            local_storage_dir = Path(".data/gcs_storage")
            local_file_path = local_storage_dir / remote_key
            
            if local_file_path.exists():
                local_file_path.unlink()
                logger.info(f"Deleted file locally: {remote_key}")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"Error deleting file locally: {e}")
            return False
    
    def _file_exists_local(self, remote_key: str) -> bool:
        """Fallback to local file system"""
        try:
            # Get local file path
            local_storage_dir = Path(".data/gcs_storage")
            local_file_path = local_storage_dir / remote_key
            
            return local_file_path.exists()
            
        except Exception as e:
            logger.error(f"Error checking file existence locally: {e}")
            return False
    
    def _list_files_local(self, prefix: str = "") -> List[str]:
        """Fallback to local file system"""
        try:
            # Get local storage directory
            local_storage_dir = Path(".data/gcs_storage")
            
            if not local_storage_dir.exists():
                return []
            
            # List files with prefix
            files = []
            for file_path in local_storage_dir.rglob("*"):
                if file_path.is_file():
                    relative_path = file_path.relative_to(local_storage_dir)
                    if str(relative_path).startswith(prefix):
                        files.append(str(relative_path))
            
            return files
            
        except Exception as e:
            logger.error(f"Error listing files locally: {e}")
            return []
    
    def _download_bytes_local(self, remote_key: str) -> bytes:
        """Fallback to local file system for bytes download"""
        try:
            # Get local file path
            local_storage_dir = Path(".data/gcs_storage")
            local_file_path = local_storage_dir / remote_key
            
            if not local_file_path.exists():
                raise FileNotFoundError(f"File {remote_key} not found locally")
            
            # Read file content
            with open(local_file_path, 'rb') as f:
                content = f.read()
            
            logger.info(f"Downloaded bytes locally: {remote_key} -> {len(content)} bytes")
            return content
            
        except Exception as e:
            logger.error(f"Error downloading bytes locally: {e}")
            raise

# Utility functions for integration
def upload_file(local_path: str, remote_key: str) -> str:
    """
    Загружает файл в GCS и возвращает публичный URL.
    
    Args:
        local_path: Локальный путь к файлу
        remote_key: Ключ для хранения в GCS
        
    Returns:
        Публичный URL файла (GCS_BASE_URL/remote_key)
    """
    provider = GoogleCloudStorageProvider()
    return provider.upload_file(local_path, remote_key)

def upload_bytes(data: bytes, remote_key: str, content_type: str = None) -> str:
    """
    Загружает данные в GCS и возвращает публичный URL.
    
    Args:
        data: Данные для загрузки
        remote_key: Ключ для хранения в GCS
        content_type: MIME тип контента
        
    Returns:
        Публичный URL файла
    """
    provider = GoogleCloudStorageProvider()
    return provider.upload_bytes(data, remote_key, content_type)

if __name__ == "__main__":
    # Test the provider
    async def test_provider():
        provider = GoogleCloudStorageProvider()
        
        # Test file upload
        test_file_path = "/tmp/test_file.txt"
        with open(test_file_path, 'w') as f:
            f.write("Test content for GCS upload")
        
        try:
            # Upload file
            url = provider.upload_file(test_file_path, "test/test_file.txt")
            print(f"Uploaded file: {url}")
            
            # Check if file exists
            exists = provider.file_exists("test/test_file.txt")
            print(f"File exists: {exists}")
            
            # List files
            files = provider.list_files("test/")
            print(f"Files with prefix 'test/': {files}")
            
            # Download file
            download_path = "/tmp/downloaded_file.txt"
            success = provider.download_file("test/test_file.txt", download_path)
            print(f"Downloaded file: {success}")
            
            # Delete file
            deleted = provider.delete_file("test/test_file.txt")
            print(f"Deleted file: {deleted}")
            
        finally:
            # Clean up test files
            import os
            try:
                os.remove(test_file_path)
                os.remove("/tmp/downloaded_file.txt")
            except:
                pass
    
    asyncio.run(test_provider())