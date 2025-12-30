"""
Integration tests for Audio API endpoints - TDD Red Phase
Following strict TDD: These tests will fail until implementation is complete.
"""

import pytest
from io import BytesIO
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from pseudoscribe.api.app import app
from pseudoscribe.api.dependencies import get_audio_processor
from pseudoscribe.infrastructure.audio_processor import AudioProcessor


TENANT_HEADER = {"X-Tenant-ID": "test-tenant"}


@pytest.fixture
def mock_audio_processor():
    """Mock AudioProcessor for testing API endpoints"""
    processor = AsyncMock(spec=AudioProcessor)
    processor.validate_format.return_value = True
    processor.validate_file_size.return_value = True
    processor.transcribe.return_value = "This is the transcribed text from the audio file."
    return processor


@pytest.fixture
def client_with_mocked_processor(db_session, mock_audio_processor):
    """Create test client with mocked audio processor"""
    from pseudoscribe.api.dependencies import get_db

    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_audio_processor] = lambda: mock_audio_processor

    yield TestClient(app)

    app.dependency_overrides.clear()


class TestAudioTranscriptionEndpoint:
    """Test suite for /api/v1/audio/transcribe endpoint"""

    # --- Endpoint Availability Tests ---

    def test_transcribe_endpoint_exists(self, client_with_mocked_processor, test_tenant):
        """Test that the transcribe endpoint is available"""
        # Try to access endpoint with no file - should get validation error, not 404
        response = client_with_mocked_processor.post(
            "/api/v1/audio/transcribe",
            headers=TENANT_HEADER
        )
        # Should not be 404 (endpoint exists)
        assert response.status_code != 404

    # --- File Upload Tests ---

    def test_upload_mp3_file_success(self, client_with_mocked_processor, test_tenant, mock_audio_processor):
        """Test successful upload of MP3 file"""
        audio_content = b"fake mp3 audio data"
        files = {"file": ("test_audio.mp3", BytesIO(audio_content), "audio/mpeg")}

        response = client_with_mocked_processor.post(
            "/api/v1/audio/transcribe",
            files=files,
            headers=TENANT_HEADER
        )

        assert response.status_code == 200
        data = response.json()
        assert "text" in data
        assert data["text"] == "This is the transcribed text from the audio file."
        assert "filename" in data
        assert data["filename"] == "test_audio.mp3"

    def test_upload_wav_file_success(self, client_with_mocked_processor, test_tenant, mock_audio_processor):
        """Test successful upload of WAV file"""
        audio_content = b"fake wav audio data"
        files = {"file": ("test_audio.wav", BytesIO(audio_content), "audio/wav")}

        response = client_with_mocked_processor.post(
            "/api/v1/audio/transcribe",
            files=files,
            headers=TENANT_HEADER
        )

        assert response.status_code == 200
        data = response.json()
        assert "text" in data
        assert data["text"] == "This is the transcribed text from the audio file."

    def test_upload_m4a_file_success(self, client_with_mocked_processor, test_tenant, mock_audio_processor):
        """Test successful upload of M4A file"""
        audio_content = b"fake m4a audio data"
        files = {"file": ("test_audio.m4a", BytesIO(audio_content), "audio/mp4")}

        response = client_with_mocked_processor.post(
            "/api/v1/audio/transcribe",
            files=files,
            headers=TENANT_HEADER
        )

        assert response.status_code == 200
        data = response.json()
        assert "text" in data

    # --- Format Validation Tests ---

    def test_upload_unsupported_format_returns_error(self, client_with_mocked_processor, test_tenant, mock_audio_processor):
        """Test that unsupported file formats return proper error"""
        from pseudoscribe.infrastructure.audio_processor import UnsupportedFormatError

        # Configure mock to raise UnsupportedFormatError
        mock_audio_processor.transcribe.side_effect = UnsupportedFormatError("Unsupported format: pdf. Supported formats: mp3, wav, m4a")

        pdf_content = b"fake pdf content"
        files = {"file": ("document.pdf", BytesIO(pdf_content), "application/pdf")}

        response = client_with_mocked_processor.post(
            "/api/v1/audio/transcribe",
            files=files,
            headers=TENANT_HEADER
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "unsupported" in data["detail"].lower() or "format" in data["detail"].lower()

    def test_upload_text_file_returns_error(self, client_with_mocked_processor, test_tenant, mock_audio_processor):
        """Test that text files are rejected"""
        from pseudoscribe.infrastructure.audio_processor import UnsupportedFormatError

        mock_audio_processor.transcribe.side_effect = UnsupportedFormatError("Unsupported format: txt")

        text_content = b"This is a text file"
        files = {"file": ("notes.txt", BytesIO(text_content), "text/plain")}

        response = client_with_mocked_processor.post(
            "/api/v1/audio/transcribe",
            files=files,
            headers=TENANT_HEADER
        )

        assert response.status_code == 400

    # --- File Size Validation Tests ---

    def test_upload_oversized_file_returns_error(self, client_with_mocked_processor, test_tenant, mock_audio_processor):
        """Test that files over 25MB are rejected"""
        from pseudoscribe.infrastructure.audio_processor import FileSizeLimitError

        mock_audio_processor.transcribe.side_effect = FileSizeLimitError("File size exceeds 25MB limit")

        # Simulate large file
        large_content = b"x" * 100  # We don't actually need to send 25MB in test
        files = {"file": ("large_audio.mp3", BytesIO(large_content), "audio/mpeg")}

        response = client_with_mocked_processor.post(
            "/api/v1/audio/transcribe",
            files=files,
            headers=TENANT_HEADER
        )

        assert response.status_code == 413  # HTTP 413 Payload Too Large
        data = response.json()
        assert "detail" in data
        assert "25mb" in data["detail"].lower() or "size" in data["detail"].lower()

    # --- Missing File Tests ---

    def test_missing_file_returns_error(self, client_with_mocked_processor, test_tenant):
        """Test that missing file in request returns proper error"""
        response = client_with_mocked_processor.post(
            "/api/v1/audio/transcribe",
            headers=TENANT_HEADER
        )

        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data

    # --- Error Handling Tests ---

    def test_transcription_api_error_returns_500(self, client_with_mocked_processor, test_tenant, mock_audio_processor):
        """Test that transcription errors return 500 with proper error message"""
        from pseudoscribe.infrastructure.audio_processor import TranscriptionError

        mock_audio_processor.transcribe.side_effect = TranscriptionError("Whisper API failed")

        audio_content = b"fake audio data"
        files = {"file": ("test.mp3", BytesIO(audio_content), "audio/mpeg")}

        response = client_with_mocked_processor.post(
            "/api/v1/audio/transcribe",
            files=files,
            headers=TENANT_HEADER
        )

        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "transcription" in data["detail"].lower() or "failed" in data["detail"].lower()

    def test_empty_audio_file_returns_empty_transcription(self, client_with_mocked_processor, test_tenant, mock_audio_processor):
        """Test that empty audio files return empty transcription"""
        mock_audio_processor.transcribe.return_value = ""

        empty_audio = b""
        files = {"file": ("empty.mp3", BytesIO(empty_audio), "audio/mpeg")}

        response = client_with_mocked_processor.post(
            "/api/v1/audio/transcribe",
            files=files,
            headers=TENANT_HEADER
        )

        assert response.status_code == 200
        data = response.json()
        assert data["text"] == ""

    # --- Tenant Isolation Tests ---

    def test_transcribe_requires_tenant_header(self, client_with_mocked_processor, test_tenant):
        """Test that requests without tenant header are rejected"""
        audio_content = b"fake audio data"
        files = {"file": ("test.mp3", BytesIO(audio_content), "audio/mpeg")}

        # Request without tenant header
        response = client_with_mocked_processor.post(
            "/api/v1/audio/transcribe",
            files=files
        )

        # Should fail due to missing tenant (middleware should catch this)
        # Exact status code depends on middleware implementation
        assert response.status_code in [400, 401, 403, 422]

    # --- Response Format Tests ---

    def test_transcribe_response_includes_metadata(self, client_with_mocked_processor, test_tenant, mock_audio_processor):
        """Test that transcription response includes all required metadata"""
        audio_content = b"fake audio data"
        files = {"file": ("test_audio.mp3", BytesIO(audio_content), "audio/mpeg")}

        response = client_with_mocked_processor.post(
            "/api/v1/audio/transcribe",
            files=files,
            headers=TENANT_HEADER
        )

        assert response.status_code == 200
        data = response.json()

        # Check all required fields are present
        assert "text" in data
        assert "filename" in data
        assert isinstance(data["text"], str)
        assert isinstance(data["filename"], str)

    # --- Integration with Audio Processor Tests ---

    def test_endpoint_calls_audio_processor_transcribe(self, client_with_mocked_processor, test_tenant, mock_audio_processor):
        """Test that endpoint properly calls AudioProcessor.transcribe()"""
        audio_content = b"fake audio data"
        files = {"file": ("test.mp3", BytesIO(audio_content), "audio/mpeg")}

        response = client_with_mocked_processor.post(
            "/api/v1/audio/transcribe",
            files=files,
            headers=TENANT_HEADER
        )

        assert response.status_code == 200
        # Verify the mock was called
        mock_audio_processor.transcribe.assert_called_once()
