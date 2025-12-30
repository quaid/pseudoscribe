"""Audio transcription API endpoints"""

from typing import Optional

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from pydantic import BaseModel, Field

from pseudoscribe.api.dependencies import get_audio_processor
from pseudoscribe.infrastructure.audio_processor import (
    AudioProcessor,
    UnsupportedFormatError,
    FileSizeLimitError,
    TranscriptionError,
)


# --- Router ---
router = APIRouter(prefix="/api/v1/audio", tags=["audio"])


# --- Pydantic Models ---


class TranscriptionResponse(BaseModel):
    """Response model for audio transcription"""
    text: str = Field(..., description="Transcribed text from audio")
    filename: str = Field(..., description="Original filename")


# --- Endpoints ---


@router.post("/transcribe", response_model=TranscriptionResponse, status_code=status.HTTP_200_OK)
async def transcribe_audio(
    file: UploadFile = File(..., description="Audio file to transcribe (mp3, wav, m4a)"),
    audio_processor: AudioProcessor = Depends(get_audio_processor),
) -> TranscriptionResponse:
    """
    Transcribe an audio file to text

    Supports the following audio formats:
    - MP3 (audio/mpeg)
    - WAV (audio/wav)
    - M4A (audio/mp4)

    Maximum file size: 25MB

    Args:
        file: Audio file to transcribe
        audio_processor: AudioProcessor instance (injected)

    Returns:
        TranscriptionResponse with transcribed text

    Raises:
        HTTPException 400: If file format is unsupported
        HTTPException 413: If file is too large
        HTTPException 500: If transcription fails
    """
    try:
        # Get filename from upload
        filename = file.filename or "audio.mp3"

        # Read file content into BytesIO
        from io import BytesIO
        file_content = await file.read()
        audio_file = BytesIO(file_content)

        # Transcribe using AudioProcessor
        transcribed_text = await audio_processor.transcribe(audio_file, filename)

        return TranscriptionResponse(
            text=transcribed_text,
            filename=filename
        )

    except UnsupportedFormatError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except FileSizeLimitError as e:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=str(e)
        )

    except TranscriptionError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transcription failed: {str(e)}"
        )

    except Exception as e:
        # Catch-all for unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during transcription: {str(e)}"
        )
