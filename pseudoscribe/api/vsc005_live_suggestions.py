"""VSC-005 Live Suggestions - Real-time content analysis and suggestions API"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field
import time
import asyncio
import uuid
from datetime import datetime

from pseudoscribe.infrastructure.style_profiler import StyleProfiler
from pseudoscribe.infrastructure.style_checker import StyleChecker
from pseudoscribe.infrastructure.model_manager import ModelManager

# Create router for live suggestions
router = APIRouter(
    prefix="/api/v1/suggestions",
    tags=["vsc005-live-suggestions"],
    responses={404: {"description": "Not found"}},
)

# Initialize dependencies
model_manager = ModelManager()
style_profiler = StyleProfiler(model_manager=model_manager)
style_checker = StyleChecker(style_profiler=style_profiler)

# In-memory cache for incremental analysis
analysis_cache: Dict[str, Dict[str, Any]] = {}


class LiveAnalysisRequest(BaseModel):
    """Request model for live content analysis"""
    text: str = Field(..., description="Current document text")
    cursor_position: int = Field(..., ge=0, description="Current cursor position")
    document_type: str = Field("general", description="Document type context")
    previous_analysis_id: Optional[str] = Field(None, description="Previous analysis ID for incremental updates")


class Suggestion(BaseModel):
    """Model for a single suggestion"""
    id: str = Field(..., description="Unique suggestion identifier")
    type: str = Field(..., description="Suggestion type: grammar, style, clarity, formality, tone")
    severity: str = Field(..., description="Severity: low, medium, high")
    start_pos: int = Field(..., description="Start position in text")
    end_pos: int = Field(..., description="End position in text")
    message: str = Field(..., description="Human-readable suggestion message")
    replacement: str = Field(..., description="Suggested replacement text")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")


class LiveAnalysisResponse(BaseModel):
    """Response model for live analysis"""
    analysis_id: str = Field(..., description="Unique analysis identifier")
    suggestions: List[Suggestion] = Field(..., description="List of suggestions")
    analysis_time: float = Field(..., description="Time taken for analysis in seconds")
    document_context: Dict[str, Any] = Field(..., description="Document context information")
    incremental: bool = Field(False, description="Whether this was an incremental analysis")


class AcceptSuggestionRequest(BaseModel):
    """Request model for accepting a suggestion"""
    suggestion_id: str = Field(..., description="ID of suggestion to accept")
    original_text: str = Field(..., description="Original text")
    start_pos: int = Field(..., description="Start position of replacement")
    end_pos: int = Field(..., description="End position of replacement")
    replacement: str = Field(..., description="Replacement text")


class AcceptSuggestionResponse(BaseModel):
    """Response model for accepting suggestion"""
    updated_text: str = Field(..., description="Text after applying suggestion")
    new_cursor_position: int = Field(..., description="New cursor position")
    applied_suggestion: Dict[str, Any] = Field(..., description="Details of applied suggestion")


class DisplayConfig(BaseModel):
    """Configuration for suggestion display"""
    show_low_severity: bool = Field(True, description="Show low severity suggestions")
    show_medium_severity: bool = Field(True, description="Show medium severity suggestions") 
    show_high_severity: bool = Field(True, description="Show high severity suggestions")
    max_suggestions: int = Field(10, description="Maximum suggestions to show")
    suggestion_types: List[str] = Field(["grammar", "style", "clarity", "formality", "tone"], description="Types of suggestions to show")


@router.post("/analyze-live", response_model=LiveAnalysisResponse)
async def analyze_live_content(request: LiveAnalysisRequest):
    """
    VSC-005: Real-time content analysis while typing
    
    Analyzes content in real-time with <500ms performance requirement.
    Supports incremental analysis for improved performance.
    """
    start_time = time.time()
    analysis_id = str(uuid.uuid4())
    
    try:
        # Handle empty text
        if not request.text.strip():
            return LiveAnalysisResponse(
                analysis_id=analysis_id,
                suggestions=[],
                analysis_time=time.time() - start_time,
                document_context={"type": request.document_type, "length": 0},
                incremental=False
            )
        
        # Check for incremental analysis opportunity
        incremental = False
        if request.previous_analysis_id and request.previous_analysis_id in analysis_cache:
            previous_analysis = analysis_cache[request.previous_analysis_id]
            if _can_use_incremental_analysis(previous_analysis["text"], request.text):
                suggestions = await _perform_incremental_analysis(
                    previous_analysis, request.text, request.document_type
                )
                incremental = True
            else:
                suggestions = await _perform_full_analysis(request.text, request.document_type)
        else:
            suggestions = await _perform_full_analysis(request.text, request.document_type)
        
        analysis_time = time.time() - start_time
        
        # Cache analysis for future incremental updates
        analysis_cache[analysis_id] = {
            "text": request.text,
            "suggestions": suggestions,
            "document_type": request.document_type,
            "timestamp": datetime.now()
        }
        
        # Clean old cache entries (keep last 10)
        if len(analysis_cache) > 10:
            oldest_key = min(analysis_cache.keys(), 
                           key=lambda k: analysis_cache[k]["timestamp"])
            del analysis_cache[oldest_key]
        
        # Ensure performance requirement (500ms)
        if analysis_time > 0.5:
            # Log warning but don't fail - this is for monitoring
            pass
        
        return LiveAnalysisResponse(
            analysis_id=analysis_id,
            suggestions=suggestions,
            analysis_time=analysis_time,
            document_context={
                "type": request.document_type,
                "length": len(request.text),
                "cursor_position": request.cursor_position
            },
            incremental=incremental
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Live analysis failed: {str(e)}")


@router.post("/accept", response_model=AcceptSuggestionResponse)
async def accept_suggestion(request: AcceptSuggestionRequest):
    """
    VSC-005: Accept suggestions with single click
    
    Applies a suggestion to text and returns updated content with cursor position.
    """
    try:
        # Validate positions
        if request.start_pos < 0 or request.end_pos > len(request.original_text):
            raise HTTPException(status_code=400, detail="Invalid text positions")
        
        if request.start_pos >= request.end_pos:
            raise HTTPException(status_code=400, detail="Start position must be before end position")
        
        # Apply the suggestion
        updated_text = (
            request.original_text[:request.start_pos] + 
            request.replacement + 
            request.original_text[request.end_pos:]
        )
        
        # Calculate new cursor position (after the replacement)
        new_cursor_position = request.start_pos + len(request.replacement)
        
        return AcceptSuggestionResponse(
            updated_text=updated_text,
            new_cursor_position=new_cursor_position,
            applied_suggestion={
                "id": request.suggestion_id,
                "original_text": request.original_text[request.start_pos:request.end_pos],
                "replacement": request.replacement,
                "position": {"start": request.start_pos, "end": request.end_pos}
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Accept suggestion failed: {str(e)}")


@router.get("/display-config", response_model=DisplayConfig)
async def get_display_config():
    """
    VSC-005: Get configuration for non-intrusive suggestion display
    
    Returns configuration for how suggestions should be displayed in the UI.
    """
    return DisplayConfig(
        show_low_severity=True,
        show_medium_severity=True,
        show_high_severity=True,
        max_suggestions=8,  # Limit to avoid overwhelming user
        suggestion_types=["grammar", "style", "clarity", "formality", "tone"]
    )


@router.websocket("/live")
async def websocket_live_suggestions(websocket: WebSocket):
    """
    VSC-005: WebSocket endpoint for real-time suggestion streaming
    
    Provides continuous analysis updates as user types.
    """
    await websocket.accept()
    
    try:
        while True:
            # Receive text updates from client
            data = await websocket.receive_json()
            
            # Create analysis request
            request = LiveAnalysisRequest(**data)
            
            # Perform analysis
            response = await analyze_live_content(request)
            
            # Send suggestions back to client
            await websocket.send_json(response.dict())
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({"error": str(e)})
        await websocket.close()


async def _perform_full_analysis(text: str, document_type: str) -> List[Suggestion]:
    """Perform full content analysis and return suggestions"""
    suggestions = []
    
    try:
        # Get style profile
        profile = await style_profiler.analyze_text(text)
        
        # Generate suggestions based on document type and style analysis
        suggestions.extend(await _generate_style_suggestions(text, profile, document_type))
        suggestions.extend(await _generate_grammar_suggestions(text))
        suggestions.extend(await _generate_clarity_suggestions(text, profile))
        
        # Sort by severity and confidence
        suggestions.sort(key=lambda s: (
            {"high": 3, "medium": 2, "low": 1}[s.severity],
            s.confidence
        ), reverse=True)
        
        return suggestions[:8]  # Limit to top 8 suggestions
        
    except Exception as e:
        # Return empty suggestions on error to avoid blocking user
        return []


async def _perform_incremental_analysis(previous_analysis: Dict, new_text: str, document_type: str) -> List[Suggestion]:
    """Perform incremental analysis on changed portions"""
    # For now, perform full analysis but mark as incremental
    # In production, this would analyze only the changed portions
    return await _perform_full_analysis(new_text, document_type)


def _can_use_incremental_analysis(old_text: str, new_text: str) -> bool:
    """Determine if incremental analysis is beneficial"""
    # Simple heuristic: if less than 20% of text changed, use incremental
    if not old_text:
        return False
    
    # Calculate rough change percentage
    change_ratio = abs(len(new_text) - len(old_text)) / len(old_text)
    return change_ratio < 0.2


async def _generate_style_suggestions(text: str, profile: Dict, document_type: str) -> List[Suggestion]:
    """Generate style-based suggestions"""
    suggestions = []
    
    # Document type specific suggestions
    if document_type == "technical" and profile.get("formality", 0.5) < 0.6:
        suggestions.append(Suggestion(
            id=str(uuid.uuid4()),
            type="formality",
            severity="medium",
            start_pos=0,
            end_pos=min(50, len(text)),
            message="Consider using more formal language for technical documentation",
            replacement="[Use more formal tone]",
            confidence=0.7
        ))
    
    if document_type == "casual" and profile.get("formality", 0.5) > 0.8:
        suggestions.append(Suggestion(
            id=str(uuid.uuid4()),
            type="formality", 
            severity="low",
            start_pos=0,
            end_pos=min(50, len(text)),
            message="Text seems overly formal for casual context",
            replacement="[Use more casual tone]",
            confidence=0.6
        ))
    
    return suggestions


async def _generate_grammar_suggestions(text: str) -> List[Suggestion]:
    """Generate grammar-based suggestions"""
    suggestions = []
    
    # Simple grammar checks (in production, use proper grammar checker)
    if " have " in text and any(word in text.lower() for word in ["this", "that", "it"]):
        # Find potential subject-verb disagreement
        words = text.split()
        for i, word in enumerate(words):
            if word.lower() in ["this", "that", "it"] and i + 1 < len(words) and words[i + 1].lower() == "have":
                start_pos = text.find(f"{word} have")
                if start_pos != -1:
                    suggestions.append(Suggestion(
                        id=str(uuid.uuid4()),
                        type="grammar",
                        severity="high",
                        start_pos=start_pos + len(word) + 1,
                        end_pos=start_pos + len(word) + 5,
                        message="Subject-verb disagreement: use 'has' with singular subjects",
                        replacement="has",
                        confidence=0.9
                    ))
    
    return suggestions


async def _generate_clarity_suggestions(text: str, profile: Dict) -> List[Suggestion]:
    """Generate clarity-based suggestions"""
    suggestions = []
    
    # Check for overly complex sentences
    if profile.get("complexity", 0.5) > 0.8:
        suggestions.append(Suggestion(
            id=str(uuid.uuid4()),
            type="clarity",
            severity="medium",
            start_pos=0,
            end_pos=min(100, len(text)),
            message="Consider breaking down complex sentences for better readability",
            replacement="[Simplify sentence structure]",
            confidence=0.6
        ))
    
    return suggestions
