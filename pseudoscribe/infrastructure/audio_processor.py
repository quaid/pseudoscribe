"""
Audio processing infrastructure for transcription
Handles audio file validation and transcription via Whisper API
"""

import os
from typing import BinaryIO, Optional
import httpx


# --- Custom Exceptions ---


class AudioProcessingError(Exception):
    """Base exception for audio processing errors"""
    pass


class UnsupportedFormatError(AudioProcessingError):
    """Raised when audio file format is not supported"""
    pass


class FileSizeLimitError(AudioProcessingError):
    """Raised when audio file exceeds size limit"""
    pass


class TranscriptionError(AudioProcessingError):
    """Raised when transcription fails"""
    pass


# --- AudioProcessor Class ---


class AudioProcessor:
    """Handles audio file processing and transcription"""

    # Supported audio formats
    SUPPORTED_FORMATS = {"mp3", "wav", "m4a"}

    # Maximum file size in bytes (25MB)
    MAX_FILE_SIZE = 25 * 1024 * 1024

    def __init__(self, whisper_url: Optional[str] = None):
        """
        Initialize AudioProcessor

        Args:
            whisper_url: URL for Whisper API service (defaults to Ollama service)
        """
        if whisper_url is None:
            # Use Ollama service URL from environment or default
            whisper_url = os.getenv("OLLAMA_BASE_URL", "http://ollama-svc:11434")

        self.whisper_url = whisper_url

    def validate_format(self, filename: str) -> bool:
        """
        Validate that the audio file format is supported

        Args:
            filename: Name of the file to validate

        Returns:
            True if format is supported

        Raises:
            UnsupportedFormatError: If format is not supported
        """
        # Extract file extension (case-insensitive)
        extension = filename.lower().split(".")[-1]

        if extension not in self.SUPPORTED_FORMATS:
            supported = ", ".join(sorted(self.SUPPORTED_FORMATS))
            raise UnsupportedFormatError(
                f"Unsupported format: {extension}. Supported formats: {supported}"
            )

        return True

    def validate_file_size(self, file: BinaryIO) -> bool:
        """
        Validate that the audio file size is within limits

        Args:
            file: File object to validate

        Returns:
            True if file size is acceptable

        Raises:
            FileSizeLimitError: If file exceeds size limit
        """
        # Get current position
        current_pos = file.tell()

        # Seek to end to get file size
        file.seek(0, 2)
        file_size = file.tell()

        # Reset to original position
        file.seek(current_pos)

        if file_size > self.MAX_FILE_SIZE:
            max_mb = self.MAX_FILE_SIZE / (1024 * 1024)
            raise FileSizeLimitError(
                f"File size exceeds {max_mb:.0f}MB limit"
            )

        return True

    async def transcribe(self, file: BinaryIO, filename: str) -> str:
        """
        Transcribe audio file to text

        Args:
            file: Audio file to transcribe
            filename: Name of the audio file

        Returns:
            Transcribed text

        Raises:
            UnsupportedFormatError: If file format is not supported
            FileSizeLimitError: If file is too large
            TranscriptionError: If transcription fails
        """
        # Validate format first
        self.validate_format(filename)

        # Validate file size
        self.validate_file_size(file)

        # Reset file pointer to beginning
        file.seek(0)

        try:
            # Call Whisper API for transcription
            transcribed_text = await self._call_whisper_api(file)
            return transcribed_text
        except TranscriptionError:
            # Re-raise our custom exception
            raise
        except Exception as e:
            # Wrap any other exceptions
            raise TranscriptionError(f"Transcription failed: {str(e)}")

    async def _call_whisper_api(self, file: BinaryIO) -> str:
        """
        Call Whisper API to transcribe audio

        This method handles the low-level HTTP communication with the Whisper service.
        It supports both Ollama-based Whisper and OpenAI-compatible Whisper endpoints.

        Args:
            file: Audio file to transcribe

        Returns:
            Transcribed text from the audio file

        Raises:
            Exception: If API call fails due to network, HTTP, or parsing errors
        """
        # Read file content
        file.seek(0)
        audio_data = file.read()

        # Construct Whisper API endpoint
        # Ollama provides Whisper via /api/transcribe endpoint
        endpoint = f"{self.whisper_url}/api/transcribe"

        # Use generous timeout for long audio files
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                # Prepare multipart form data
                files = {"file": audio_data}

                # Make request to Whisper API
                response = await client.post(endpoint, files=files)

                # Check for successful response
                if response.status_code != 200:
                    raise Exception(
                        f"Whisper API returned status {response.status_code}: {response.text}"
                    )

                # Parse JSON response
                result = response.json()

                # Extract transcribed text
                # Different Whisper implementations may use different response formats
                # Try 'text' first (OpenAI format), fall back to 'transcription'
                text = result.get("text", result.get("transcription", ""))

                return text

            except httpx.HTTPError as e:
                raise Exception(f"HTTP error calling Whisper API: {str(e)}")
            except Exception as e:
                raise Exception(f"Error calling Whisper API: {str(e)}")
