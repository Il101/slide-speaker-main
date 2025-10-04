"""Secrets management for Slide Speaker"""
import os
import json
import logging
from typing import Optional, Dict, Any, Union
from pathlib import Path
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)

class SecretsManager:
    """Centralized secrets management"""
    
    def __init__(self, master_key: Optional[str] = None):
        self.master_key = master_key or os.getenv("SECRETS_MASTER_KEY")
        self.secrets_file = Path(os.getenv("SECRETS_FILE", ".secrets"))
        self._fernet = None
        self._load_secrets()
    
    def _get_fernet(self) -> Fernet:
        """Get or create Fernet instance for encryption"""
        if self._fernet is None:
            if not self.master_key:
                raise ValueError("Master key not provided")
            
            # Derive key from master key
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'slide_speaker_salt',  # In production, use random salt
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(self.master_key.encode()))
            self._fernet = Fernet(key)
        
        return self._fernet
    
    def _load_secrets(self):
        """Load secrets from file"""
        if self.secrets_file.exists():
            try:
                with open(self.secrets_file, 'rb') as f:
                    encrypted_data = f.read()
                
                if encrypted_data:
                    fernet = self._get_fernet()
                    decrypted_data = fernet.decrypt(encrypted_data)
                    self._secrets = json.loads(decrypted_data.decode())
                else:
                    self._secrets = {}
            except Exception as e:
                logger.error(f"Failed to load secrets: {e}")
                self._secrets = {}
        else:
            self._secrets = {}
    
    def _save_secrets(self):
        """Save secrets to file"""
        try:
            fernet = self._get_fernet()
            encrypted_data = fernet.encrypt(json.dumps(self._secrets).encode())
            
            # Ensure directory exists
            self.secrets_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.secrets_file, 'wb') as f:
                f.write(encrypted_data)
            
            # Set restrictive permissions
            self.secrets_file.chmod(0o600)
            
        except Exception as e:
            logger.error(f"Failed to save secrets: {e}")
            raise
    
    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a secret value"""
        return self._secrets.get(key, default)
    
    def set_secret(self, key: str, value: str):
        """Set a secret value"""
        self._secrets[key] = value
        self._save_secrets()
    
    def delete_secret(self, key: str):
        """Delete a secret"""
        if key in self._secrets:
            del self._secrets[key]
            self._save_secrets()
    
    def list_secrets(self) -> Dict[str, Any]:
        """List all secret keys (without values)"""
        return {key: "***" for key in self._secrets.keys()}
    
    def get_database_url(self) -> str:
        """Get database URL from secrets"""
        return self.get_secret("DATABASE_URL") or os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/slide_speaker")
    
    def get_redis_url(self) -> str:
        """Get Redis URL from secrets"""
        return self.get_secret("REDIS_URL") or os.getenv("REDIS_URL", "redis://localhost:6379")
    
    def get_jwt_secret(self) -> str:
        """Get JWT secret from secrets"""
        return self.get_secret("JWT_SECRET_KEY") or os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    
    def get_openai_key(self) -> Optional[str]:
        """Get OpenAI API key from secrets"""
        return self.get_secret("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
    
    def get_azure_tts_key(self) -> Optional[str]:
        """Get Azure TTS key from secrets"""
        return self.get_secret("AZURE_TTS_KEY") or os.getenv("AZURE_TTS_KEY")
    
    def get_minio_credentials(self) -> tuple[str, str]:
        """Get MinIO credentials from secrets"""
        access_key = self.get_secret("MINIO_ROOT_USER") or os.getenv("MINIO_ROOT_USER", "minioadmin")
        secret_key = self.get_secret("MINIO_ROOT_PASSWORD") or os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")
        return access_key, secret_key
    
    def get_cors_origins(self) -> str:
        """Get CORS origins from secrets"""
        return self.get_secret("CORS_ORIGINS") or os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173")
    
    def get_grafana_password(self) -> str:
        """Get Grafana password from secrets"""
        return self.get_secret("GRAFANA_PASSWORD") or os.getenv("GRAFANA_PASSWORD", "admin")

# Global secrets manager instance
secrets_manager = SecretsManager()

# Convenience functions
def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get a secret value"""
    return secrets_manager.get_secret(key, default)

def set_secret(key: str, value: str):
    """Set a secret value"""
    secrets_manager.set_secret(key, value)

def get_database_url() -> str:
    """Get database URL"""
    return secrets_manager.get_database_url()

def get_redis_url() -> str:
    """Get Redis URL"""
    return secrets_manager.get_redis_url()

def get_jwt_secret() -> str:
    """Get JWT secret"""
    return secrets_manager.get_jwt_secret()

def get_openai_key() -> Optional[str]:
    """Get OpenAI API key"""
    return secrets_manager.get_openai_key()

def get_azure_tts_key() -> Optional[str]:
    """Get Azure TTS key"""
    return secrets_manager.get_azure_tts_key()

def get_minio_credentials() -> tuple[str, str]:
    """Get MinIO credentials"""
    return secrets_manager.get_minio_credentials()

def get_cors_origins() -> str:
    """Get CORS origins"""
    return secrets_manager.get_cors_origins()

def get_grafana_password() -> str:
    """Get Grafana password"""
    return secrets_manager.get_grafana_password()

# CLI commands for secrets management
def init_secrets(master_key: str):
    """Initialize secrets with master key"""
    global secrets_manager
    secrets_manager = SecretsManager(master_key)
    logger.info("Secrets manager initialized")

def migrate_env_to_secrets():
    """Migrate environment variables to secrets"""
    env_vars = [
        "DATABASE_URL",
        "REDIS_URL", 
        "JWT_SECRET_KEY",
        "OPENAI_API_KEY",
        "AZURE_TTS_KEY",
        "MINIO_ROOT_USER",
        "MINIO_ROOT_PASSWORD",
        "CORS_ORIGINS",
        "GRAFANA_PASSWORD"
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value and not secrets_manager.get_secret(var):
            secrets_manager.set_secret(var, value)
            logger.info(f"Migrated {var} to secrets")
    
    logger.info("Migration completed")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m app.core.secrets <command> [args]")
        print("Commands:")
        print("  init <master_key>     - Initialize secrets with master key")
        print("  get <key>             - Get secret value")
        print("  set <key> <value>     - Set secret value")
        print("  list                  - List all secrets")
        print("  migrate               - Migrate env vars to secrets")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "init":
        if len(sys.argv) < 3:
            print("Usage: init <master_key>")
            sys.exit(1)
        init_secrets(sys.argv[2])
        print("Secrets initialized")
    
    elif command == "get":
        if len(sys.argv) < 3:
            print("Usage: get <key>")
            sys.exit(1)
        value = get_secret(sys.argv[2])
        print(value if value else "Secret not found")
    
    elif command == "set":
        if len(sys.argv) < 4:
            print("Usage: set <key> <value>")
            sys.exit(1)
        set_secret(sys.argv[2], sys.argv[3])
        print("Secret set")
    
    elif command == "list":
        secrets = secrets_manager.list_secrets()
        for key, value in secrets.items():
            print(f"{key}: {value}")
    
    elif command == "migrate":
        migrate_env_to_secrets()
        print("Migration completed")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
