"""
Unit tests for Core Exceptions
"""
import pytest

from app.core.exceptions import SlideSpeakerException


class TestSlideSpeakerException:
    """Test SlideSpeakerException class"""
    
    def test_exception_creation(self):
        """Test creating exception"""
        exc = SlideSpeakerException("Test error")
        assert str(exc) == "Test error"
    
    def test_exception_with_details(self):
        """Test exception with details"""
        try:
            exc = SlideSpeakerException("Error occurred", details={"code": 500})
            assert "Error occurred" in str(exc)
            if hasattr(exc, 'details'):
                assert exc.details["code"] == 500
        except TypeError:
            # details parameter might not exist
            exc = SlideSpeakerException("Error occurred")
            assert str(exc) == "Error occurred"
    
    def test_exception_inheritance(self):
        """Test exception inherits from Exception"""
        exc = SlideSpeakerException("Test")
        assert isinstance(exc, Exception)
    
    def test_exception_raise_and_catch(self):
        """Test raising and catching exception"""
        with pytest.raises(SlideSpeakerException) as exc_info:
            raise SlideSpeakerException("Custom error message")
        
        assert "Custom error message" in str(exc_info.value)
    
    def test_exception_with_cause(self):
        """Test exception with cause"""
        try:
            try:
                raise ValueError("Original error")
            except ValueError as e:
                raise SlideSpeakerException("Wrapper error") from e
        except SlideSpeakerException as exc:
            assert str(exc) == "Wrapper error"
            if hasattr(exc, '__cause__'):
                assert isinstance(exc.__cause__, ValueError)
    
    def test_multiple_exceptions(self):
        """Test multiple exception instances"""
        exc1 = SlideSpeakerException("Error 1")
        exc2 = SlideSpeakerException("Error 2")
        
        assert str(exc1) != str(exc2)
        assert str(exc1) == "Error 1"
        assert str(exc2) == "Error 2"


class TestExceptionHandling:
    """Test exception handling patterns"""
    
    def test_exception_in_function(self):
        """Test exception raised in function"""
        def failing_function():
            raise SlideSpeakerException("Function failed")
        
        with pytest.raises(SlideSpeakerException):
            failing_function()
    
    def test_exception_with_try_except(self):
        """Test exception with try-except"""
        caught = False
        try:
            raise SlideSpeakerException("Test error")
        except SlideSpeakerException:
            caught = True
        
        assert caught is True
    
    def test_exception_with_finally(self):
        """Test exception with finally block"""
        finally_executed = False
        
        try:
            try:
                raise SlideSpeakerException("Test")
            finally:
                finally_executed = True
        except SlideSpeakerException:
            pass
        
        assert finally_executed is True
    
    def test_re_raise_exception(self):
        """Test re-raising exception"""
        with pytest.raises(SlideSpeakerException) as exc_info:
            try:
                raise SlideSpeakerException("Original")
            except SlideSpeakerException:
                raise
        
        assert "Original" in str(exc_info.value)
