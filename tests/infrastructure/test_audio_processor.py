"""
Unit tests for AudioProcessor - TDD Red Phase
Following strict TDD: These tests will fail until implementation is complete.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from io import BytesIO

from pseudoscribe.infrastructure.audio_processor import (
    AudioProcessor,
    AudioProcessingError,
    UnsupportedFormatError,
    FileSizeLimitError,
    TranscriptionError,
)


class TestAudioProcessor:
    """Test suite for AudioProcessor class"""

    @pytest.fixture
    def audio_processor(self):
        """Create AudioProcessor instance for testing"""
        return AudioProcessor()

    @pytest.fixture
    def mock_audio_file(self):
        """Create a mock audio file for testing"""
        return BytesIO(b"fake audio content")

    # --- Format Validation Tests ---

    @pytest.mark.asyncio
    async def test_validate_format_accepts_mp3(self, audio_processor):
        """Test that MP3 format is accepted"""
        result = audio_processor.validate_format("test.mp3")
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_format_accepts_wav(self, audio_processor):
        """Test that WAV format is accepted"""
        result = audio_processor.validate_format("test.wav")
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_format_accepts_m4a(self, audio_processor):
        """Test that M4A format is accepted"""
        result = audio_processor.validate_format("test.m4a")
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_format_rejects_unsupported(self, audio_processor):
        """Test that unsupported formats are rejected"""
        with pytest.raises(UnsupportedFormatError) as exc_info:
            audio_processor.validate_format("test.pdf")
        assert "pdf" in str(exc_info.value).lower()
        assert "supported formats" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_validate_format_case_insensitive(self, audio_processor):
        """Test that format validation is case-insensitive"""
        result = audio_processor.validate_format("test.MP3")
        assert result is True

    # --- File Size Validation Tests ---

    @pytest.mark.asyncio
    async def test_validate_file_size_accepts_valid_size(self, audio_processor):
        """Test that files under 25MB are accepted"""
        # 10MB file
        file_content = BytesIO(b"x" * (10 * 1024 * 1024))
        result = audio_processor.validate_file_size(file_content)
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_file_size_rejects_oversized(self, audio_processor):
        """Test that files over 25MB are rejected"""
        # 30MB file
        file_content = BytesIO(b"x" * (30 * 1024 * 1024))
        with pytest.raises(FileSizeLimitError) as exc_info:
            audio_processor.validate_file_size(file_content)
        assert "25mb" in str(exc_info.value).lower() or "25 mb" in str(exc_info.value).lower()

    # --- Transcription Tests ---

    @pytest.mark.asyncio
    async def test_transcribe_returns_text(self, audio_processor, mock_audio_file):
        """Test that transcribe method returns transcribed text"""
        with patch.object(audio_processor, '_call_whisper_api', new_callable=AsyncMock) as mock_whisper:
            mock_whisper.return_value = "This is transcribed text from the audio file."

            result = await audio_processor.transcribe(mock_audio_file, "test.mp3")

            assert isinstance(result, str)
            assert result == "This is transcribed text from the audio file."
            mock_whisper.assert_called_once()

    @pytest.mark.asyncio
    async def test_transcribe_validates_format_before_processing(self, audio_processor, mock_audio_file):
        """Test that transcribe validates file format before processing"""
        with pytest.raises(UnsupportedFormatError):
            await audio_processor.transcribe(mock_audio_file, "test.txt")

    @pytest.mark.asyncio
    async def test_transcribe_validates_file_size_before_processing(self, audio_processor):
        """Test that transcribe validates file size before processing"""
        oversized_file = BytesIO(b"x" * (30 * 1024 * 1024))
        with pytest.raises(FileSizeLimitError):
            await audio_processor.transcribe(oversized_file, "test.mp3")

    @pytest.mark.asyncio
    async def test_transcribe_handles_whisper_api_error(self, audio_processor, mock_audio_file):
        """Test that transcribe handles Whisper API errors gracefully"""
        with patch.object(audio_processor, '_call_whisper_api', new_callable=AsyncMock) as mock_whisper:
            mock_whisper.side_effect = Exception("Whisper API error")

            with pytest.raises(TranscriptionError) as exc_info:
                await audio_processor.transcribe(mock_audio_file, "test.mp3")

            assert "transcription failed" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_transcribe_with_empty_audio_returns_empty_string(self, audio_processor):
        """Test that empty audio file returns empty transcription"""
        empty_file = BytesIO(b"")
        with patch.object(audio_processor, '_call_whisper_api', new_callable=AsyncMock) as mock_whisper:
            mock_whisper.return_value = ""

            result = await audio_processor.transcribe(empty_file, "test.mp3")
            assert result == ""

    # --- Whisper API Integration Tests ---

    @pytest.mark.asyncio
    async def test_call_whisper_api_uses_ollama_by_default(self, audio_processor, mock_audio_file):
        """Test that Whisper API uses Ollama service by default"""
        with patch('pseudoscribe.infrastructure.audio_processor.httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"text": "transcribed text"}

            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None
            mock_client_instance.post.return_value = mock_response
            mock_client.return_value = mock_client_instance

            result = await audio_processor._call_whisper_api(mock_audio_file)

            assert result == "transcribed text"

    @pytest.mark.asyncio
    async def test_call_whisper_api_handles_network_error(self, audio_processor, mock_audio_file):
        """Test that Whisper API handles network errors"""
        with patch('pseudoscribe.infrastructure.audio_processor.httpx.AsyncClient') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None
            mock_client_instance.post.side_effect = Exception("Network error")
            mock_client.return_value = mock_client_instance

            with pytest.raises(Exception):
                await audio_processor._call_whisper_api(mock_audio_file)

    @pytest.mark.asyncio
    async def test_call_whisper_api_handles_non_200_response(self, audio_processor, mock_audio_file):
        """Test that Whisper API handles non-200 status codes"""
        with patch('pseudoscribe.infrastructure.audio_processor.httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"

            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None
            mock_client_instance.post.return_value = mock_response
            mock_client.return_value = mock_client_instance

            with pytest.raises(Exception):
                await audio_processor._call_whisper_api(mock_audio_file)

    # --- Configuration Tests ---

    @pytest.mark.asyncio
    async def test_audio_processor_respects_custom_whisper_url(self):
        """Test that AudioProcessor uses custom Whisper URL when provided"""
        custom_url = "http://custom-whisper:8000"
        processor = AudioProcessor(whisper_url=custom_url)
        assert processor.whisper_url == custom_url

    @pytest.mark.asyncio
    async def test_audio_processor_uses_default_whisper_url(self):
        """Test that AudioProcessor uses default Whisper URL"""
        processor = AudioProcessor()
        # Should use Ollama service URL by default
        assert "ollama" in processor.whisper_url.lower() or "11434" in processor.whisper_url
