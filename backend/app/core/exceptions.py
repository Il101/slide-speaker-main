"""Custom exceptions for the application"""

class SlideSpeakerException(Exception):
    """Base exception for Slide Speaker"""
    pass

class FileProcessingError(SlideSpeakerException):
    """Error during file processing"""
    pass

class ParsingError(SlideSpeakerException):
    """Error during document parsing"""
    pass

class AIGenerationError(SlideSpeakerException):
    """Error during AI content generation"""
    pass

class ExportError(SlideSpeakerException):
    """Error during video export"""
    pass

class ValidationError(SlideSpeakerException):
    """Error during data validation"""
    pass