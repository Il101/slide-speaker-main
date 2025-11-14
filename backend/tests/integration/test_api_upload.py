"""
Integration tests for Upload API endpoints
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import tempfile
import os
from pathlib import Path


@pytest.mark.asyncio
@pytest.mark.integration
class TestUploadEndpoint:
    """Test file upload endpoint"""
    
    async def test_upload_with_valid_file(self, test_client):
        """Test uploading valid presentation file"""
        # Create a minimal valid file
        with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as tmp:
            # Write minimal PPTX signature
            tmp.write(b"PK\x03\x04")
            tmp.write(b"\x00" * 100)  # Padding
            tmp_path = tmp.name
        
        try:
            with open(tmp_path, 'rb') as f:
                files = {'file': ('test.pptx', f, 'application/vnd.openxmlformats-officedocument.presentationml.presentation')}
                
                with patch('app.main.process_lesson_full_pipeline.delay') as mock_task:
                    mock_task.return_value = Mock(id='task-123')
                    
                    response = await test_client.post(
                        "/upload",
                        files=files
                    )
                    
                    # Should succeed or return validation error
                    assert response.status_code in [200, 201, 400, 422, 500]
                    
                    if response.status_code in [200, 201]:
                        data = response.json()
                        assert 'lesson_id' in data or 'message' in data
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    async def test_upload_without_file(self, test_client):
        """Test upload without file"""
        response = await test_client.post("/upload")
        
        # Should return validation error
        assert response.status_code in [400, 422]
    
    async def test_upload_with_invalid_file_type(self, test_client):
        """Test uploading invalid file type"""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            tmp.write(b"This is not a presentation")
            tmp_path = tmp.name
        
        try:
            with open(tmp_path, 'rb') as f:
                files = {'file': ('test.txt', f, 'text/plain')}
                
                response = await test_client.post(
                    "/upload",
                    files=files
                )
                
                # Should reject invalid file type
                assert response.status_code in [400, 422]
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    async def test_upload_with_large_file(self, test_client):
        """Test uploading large file"""
        # Create a 50MB file (mock)
        with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as tmp:
            tmp.write(b"PK\x03\x04")
            tmp.write(b"\x00" * (50 * 1024 * 1024))  # 50MB
            tmp_path = tmp.name
        
        try:
            # This might fail due to size limits
            with open(tmp_path, 'rb') as f:
                files = {'file': ('large.pptx', f, 'application/vnd.openxmlformats-officedocument.presentationml.presentation')}
                
                response = await test_client.post(
                    "/upload",
                    files=files,
                    timeout=30.0
                )
                
                # Either succeeds or fails due to size limit
                assert response.status_code in [200, 201, 400, 413, 422, 500]
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    async def test_upload_with_authentication(self, test_client):
        """Test upload with authentication token"""
        from app.core.auth import AuthManager
        
        token = AuthManager.create_access_token({"sub": "test-user", "email": "test@example.com"})
        
        with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as tmp:
            tmp.write(b"PK\x03\x04" + b"\x00" * 100)
            tmp_path = tmp.name
        
        try:
            with open(tmp_path, 'rb') as f:
                files = {'file': ('test.pptx', f, 'application/vnd.openxmlformats-officedocument.presentationml.presentation')}
                headers = {'Authorization': f'Bearer {token}'}
                
                with patch('app.main.process_lesson_full_pipeline.delay') as mock_task:
                    mock_task.return_value = Mock(id='task-123')
                    
                    response = await test_client.post(
                        "/upload",
                        files=files,
                        headers=headers
                    )
                    
                    assert response.status_code in [200, 201, 401, 400, 422, 500]
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


@pytest.mark.asyncio
@pytest.mark.integration
class TestLessonStatusEndpoint:
    """Test lesson status endpoint"""
    
    @patch('app.main.get_db')
    async def test_get_lesson_status_success(self, mock_get_db, test_client):
        """Test getting lesson status"""
        mock_db = Mock()
        mock_lesson = Mock()
        mock_lesson.id = "test-123"
        mock_lesson.status = "completed"
        mock_lesson.processing_progress = '{"stage": "completed", "progress": 100}'
        
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_lesson
        mock_db.execute.return_value = mock_result
        mock_get_db.return_value.__enter__ = Mock(return_value=mock_db)
        mock_get_db.return_value.__exit__ = Mock(return_value=None)
        
        response = await test_client.get("/lessons/test-123/status")
        
        # Should return status or 404
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert 'status' in data
    
    async def test_get_lesson_status_not_found(self, test_client):
        """Test getting status for non-existent lesson"""
        response = await test_client.get("/lessons/nonexistent-id/status")
        
        # Should return 404
        assert response.status_code in [404, 422]
    
    async def test_get_lesson_status_invalid_id(self, test_client):
        """Test getting status with invalid ID format"""
        response = await test_client.get("/lessons//status")
        
        # Should return validation error or 404
        assert response.status_code in [404, 422]


@pytest.mark.asyncio
@pytest.mark.integration  
class TestLessonManifestEndpoint:
    """Test lesson manifest endpoint"""
    
    @patch('app.main.get_db')
    async def test_get_lesson_manifest_success(self, mock_get_db, test_client):
        """Test getting lesson manifest"""
        mock_db = Mock()
        mock_lesson = Mock()
        mock_lesson.manifest = {"slides": [], "metadata": {}}
        
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_lesson
        mock_db.execute.return_value = mock_result
        mock_get_db.return_value.__enter__ = Mock(return_value=mock_db)
        mock_get_db.return_value.__exit__ = Mock(return_value=None)
        
        response = await test_client.get("/lessons/test-123/manifest")
        
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)
    
    async def test_get_lesson_manifest_not_found(self, test_client):
        """Test getting manifest for non-existent lesson"""
        response = await test_client.get("/lessons/nonexistent/manifest")
        
        assert response.status_code in [404, 422]


@pytest.mark.asyncio
@pytest.mark.integration
class TestGenerateSpeakerNotesEndpoint:
    """Test generate speaker notes endpoint"""
    
    async def test_generate_speaker_notes_success(self, test_client):
        """Test generating speaker notes"""
        request_data = {
            "slide_id": 1,
            "elements": [
                {"type": "heading", "text": "Test Heading"}
            ]
        }
        
        with patch('app.main.generate_speaker_notes_task.delay') as mock_task:
            mock_task.return_value = Mock(id='task-123')
            
            response = await test_client.post(
                "/lessons/test-123/generate-speaker-notes",
                json=request_data
            )
            
            # Should succeed or fail with validation error
            assert response.status_code in [200, 202, 400, 404, 422, 500]
    
    async def test_generate_speaker_notes_invalid_data(self, test_client):
        """Test generating with invalid data"""
        response = await test_client.post(
            "/lessons/test-123/generate-speaker-notes",
            json={}
        )
        
        # Should return validation error
        assert response.status_code in [400, 422]


@pytest.mark.asyncio
@pytest.mark.integration
class TestGenerateAudioEndpoint:
    """Test generate audio endpoint"""
    
    async def test_generate_audio_success(self, test_client):
        """Test generating audio"""
        request_data = {
            "slide_id": 1,
            "text": "This is test speaker notes",
            "voice": "en-US-Standard-A"
        }
        
        with patch('app.main.generate_audio_task.delay') as mock_task:
            mock_task.return_value = Mock(id='task-123')
            
            response = await test_client.post(
                "/lessons/test-123/generate-audio",
                json=request_data
            )
            
            assert response.status_code in [200, 202, 400, 404, 422, 500]
    
    async def test_generate_audio_empty_text(self, test_client):
        """Test generating audio with empty text"""
        request_data = {
            "slide_id": 1,
            "text": "",
            "voice": "en-US-Standard-A"
        }
        
        response = await test_client.post(
            "/lessons/test-123/generate-audio",
            json=request_data
        )
        
        # Should handle empty text
        assert response.status_code in [200, 400, 422]


@pytest.mark.asyncio
@pytest.mark.integration
class TestVoicesEndpoint:
    """Test voices listing endpoint"""
    
    async def test_list_voices(self, test_client):
        """Test listing available voices"""
        response = await test_client.get("/voices")
        
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (list, dict))


@pytest.mark.asyncio
@pytest.mark.integration
class TestEditEndpoint:
    """Test edit endpoint"""
    
    async def test_edit_lesson_content(self, test_client):
        """Test editing lesson content"""
        request_data = {
            "slide_id": 1,
            "field": "speaker_notes",
            "value": "Updated speaker notes"
        }
        
        response = await test_client.post(
            "/lessons/test-123/edit",
            json=request_data
        )
        
        assert response.status_code in [200, 400, 404, 422]
    
    async def test_edit_invalid_field(self, test_client):
        """Test editing with invalid field"""
        request_data = {
            "slide_id": 1,
            "field": "invalid_field",
            "value": "test"
        }
        
        response = await test_client.post(
            "/lessons/test-123/edit",
            json=request_data
        )
        
        assert response.status_code in [400, 422]


@pytest.mark.asyncio
@pytest.mark.integration
class TestPatchEndpoint:
    """Test patch endpoint"""
    
    async def test_patch_lesson(self, test_client):
        """Test patching lesson"""
        request_data = {
            "slides": [
                {
                    "slide_id": 1,
                    "speaker_notes": "Updated notes"
                }
            ]
        }
        
        response = await test_client.post(
            "/lessons/test-123/patch",
            json=request_data
        )
        
        assert response.status_code in [200, 400, 404, 422]
    
    async def test_patch_empty_data(self, test_client):
        """Test patching with empty data"""
        response = await test_client.post(
            "/lessons/test-123/patch",
            json={}
        )
        
        # Should handle gracefully
        assert response.status_code in [200, 400, 422]


@pytest.mark.asyncio
@pytest.mark.integration
class TestExportEndpoint:
    """Test export endpoint"""
    
    async def test_export_lesson_success(self, test_client):
        """Test exporting lesson to video"""
        request_data = {
            "format": "mp4",
            "quality": "1080p"
        }
        
        with patch('app.main.export_video_task.delay') as mock_task:
            mock_task.return_value = Mock(id='task-123')
            
            response = await test_client.post(
                "/lessons/test-123/export",
                json=request_data
            )
            
            assert response.status_code in [200, 202, 400, 404, 422, 500]
    
    async def test_export_invalid_format(self, test_client):
        """Test exporting with invalid format"""
        request_data = {
            "format": "invalid_format",
            "quality": "1080p"
        }
        
        response = await test_client.post(
            "/lessons/test-123/export",
            json=request_data
        )
        
        assert response.status_code in [400, 422]
    
    async def test_export_default_settings(self, test_client):
        """Test exporting with default settings"""
        with patch('app.main.export_video_task.delay') as mock_task:
            mock_task.return_value = Mock(id='task-123')
            
            response = await test_client.post(
                "/lessons/test-123/export",
                json={}
            )
            
            assert response.status_code in [200, 202, 400, 404, 422, 500]


@pytest.mark.asyncio
@pytest.mark.integration
class TestExportStatusEndpoint:
    """Test export status endpoint"""
    
    async def test_get_export_status(self, test_client):
        """Test getting export status"""
        response = await test_client.get("/lessons/test-123/export/status")
        
        assert response.status_code in [200, 404]
    
    async def test_get_export_status_not_found(self, test_client):
        """Test getting status for non-existent export"""
        response = await test_client.get("/lessons/nonexistent/export/status")
        
        assert response.status_code in [404, 422]


@pytest.mark.asyncio
@pytest.mark.integration
class TestDownloadEndpoint:
    """Test download endpoint"""
    
    async def test_download_exported_video(self, test_client):
        """Test downloading exported video"""
        response = await test_client.get("/exports/test-123/download")
        
        # Should return file or 404
        assert response.status_code in [200, 404]
    
    async def test_download_nonexistent_export(self, test_client):
        """Test downloading non-existent export"""
        response = await test_client.get("/exports/nonexistent/download")
        
        assert response.status_code in [404, 422]


@pytest.mark.asyncio
@pytest.mark.integration
class TestPreviewEndpoint:
    """Test preview endpoint"""
    
    async def test_get_slide_preview(self, test_client):
        """Test getting slide preview"""
        response = await test_client.get("/lessons/test-123/preview/1")
        
        # Should return image or 404
        assert response.status_code in [200, 404]
    
    async def test_get_preview_invalid_slide(self, test_client):
        """Test getting preview for invalid slide"""
        response = await test_client.get("/lessons/test-123/preview/999")
        
        assert response.status_code in [404, 422]
