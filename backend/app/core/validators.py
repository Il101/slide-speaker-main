"""API keys validation and password strength validation"""
import os
import re
import logging
import uuid
from pathlib import Path
from typing import List, Tuple
from fastapi import HTTPException

logger = logging.getLogger(__name__)


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validate password strength
    
    Requirements:
    - Minimum 8 characters
    - At least 1 uppercase letter
    - At least 1 lowercase letter
    - At least 1 digit
    - At least 1 special character
    
    Args:
        password: Password to validate
        
    Returns:
        (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit"
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=\[\]\\\/~`]", password):
        return False, "Password must contain at least one special character (!@#$%^&*...)"
    
    # Check for common weak passwords
    common_passwords = [
        "password", "123456", "12345678", "qwerty", "abc123",
        "monkey", "1234567", "letmein", "trustno1", "dragon"
    ]
    if password.lower() in common_passwords:
        return False, "Password is too common. Please choose a stronger password."
    
    return True, "Password is strong"


class APIKeyValidator:
    """Validates that required API keys and credentials are set"""
    
    @staticmethod
    def validate_google_credentials() -> Tuple[bool, str]:
        """Validate Google Cloud credentials"""
        creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        
        if not creds_path:
            return False, "GOOGLE_APPLICATION_CREDENTIALS environment variable not set"
        
        creds_file = Path(creds_path)
        if not creds_file.exists():
            return False, f"Google credentials file not found: {creds_path}"
        
        # Check if file is valid JSON
        try:
            import json
            with open(creds_file, 'r') as f:
                creds_data = json.load(f)
                
            if 'type' not in creds_data or creds_data['type'] != 'service_account':
                return False, f"Invalid credentials file format: {creds_path}"
                
            if 'project_id' not in creds_data:
                return False, "Missing project_id in credentials file"
            
            logger.info(f"✅ Google credentials valid: project={creds_data.get('project_id')}")
            return True, "OK"
            
        except Exception as e:
            return False, f"Failed to parse credentials file: {e}"
    
    @staticmethod
    def validate_openrouter_key() -> Tuple[bool, str]:
        """Validate OpenRouter API key"""
        api_key = os.getenv("OPENROUTER_API_KEY")
        
        if not api_key:
            return False, "OPENROUTER_API_KEY not set (optional)"
        
        if not api_key.startswith("sk-"):
            return False, f"Invalid OpenRouter API key format"
        
        logger.info("✅ OpenRouter API key found")
        return True, "OK"
    
    @staticmethod
    def validate_required_settings() -> Tuple[bool, List[str]]:
        """Validate all required settings for pipeline"""
        errors = []
        warnings = []
        
        # Check LLM provider
        llm_provider = os.getenv("LLM_PROVIDER", "openrouter")
        
        if llm_provider == "gemini":
            is_valid, msg = APIKeyValidator.validate_google_credentials()
            if not is_valid:
                errors.append(f"Gemini LLM: {msg}")
        elif llm_provider == "openrouter":
            is_valid, msg = APIKeyValidator.validate_openrouter_key()
            if not is_valid:
                warnings.append(f"OpenRouter LLM: {msg}")
        
        # Check OCR provider
        ocr_provider = os.getenv("OCR_PROVIDER", "vision")
        if ocr_provider in ["vision", "google"]:
            is_valid, msg = APIKeyValidator.validate_google_credentials()
            if not is_valid:
                errors.append(f"OCR ({ocr_provider}): {msg}")
        
        # Check TTS provider
        tts_provider = os.getenv("TTS_PROVIDER", "google")
        if tts_provider == "google":
            is_valid, msg = APIKeyValidator.validate_google_credentials()
            if not is_valid:
                errors.append(f"TTS (google): {msg}")
        
        # Check GCP project ID
        gcp_project = os.getenv("GCP_PROJECT_ID")
        if not gcp_project and ocr_provider in ["vision", "google"]:
            errors.append("GCP_PROJECT_ID not set (required for Google Cloud services)")
        
        # Log results
        if errors:
            logger.error("❌ API validation failed:")
            for error in errors:
                logger.error(f"  - {error}")
        
        if warnings:
            logger.warning("⚠️ API validation warnings:")
            for warning in warnings:
                logger.warning(f"  - {warning}")
        
        if not errors and not warnings:
            logger.info("✅ All API credentials validated successfully")
        
        return len(errors) == 0, errors + warnings
    
    @staticmethod
    def validate_or_fail():
        """Validate API keys and fail if critical ones are missing"""
        is_valid, messages = APIKeyValidator.validate_required_settings()
        
        # Allow to run in mock mode if ALLOW_MOCK_MODE=true
        allow_mock = os.getenv("ALLOW_MOCK_MODE", "false").lower() in ("true", "1", "yes")
        
        if not is_valid:
            if allow_mock:
                logger.warning("⚠️ Running in MOCK MODE (ALLOW_MOCK_MODE=true)")
                logger.warning("⚠️ API calls will be simulated, results may not be accurate")
                return
            else:
                logger.error("❌ Critical API credentials missing!")
                logger.error("Set ALLOW_MOCK_MODE=true to run in mock mode (not recommended for production)")
                raise RuntimeError(f"API validation failed: {', '.join(messages)}")


def validate_api_keys():
    """Main validation function to be called on startup"""
    try:
        APIKeyValidator.validate_or_fail()
    except Exception as e:
        logger.error(f"API validation error: {e}")
        raise


def validate_lesson_id(lesson_id: str) -> str:
    """
    Validate that lesson_id is a valid UUID v4
    Prevents path traversal attacks
    
    Args:
        lesson_id: Lesson ID string to validate
        
    Returns:
        Validated lesson_id as string
        
    Raises:
        HTTPException 400: If lesson_id is not a valid UUID v4
    """
    try:
        uuid_obj = uuid.UUID(lesson_id, version=4)
        return str(uuid_obj)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid lesson_id format. Must be a valid UUID."
        )
