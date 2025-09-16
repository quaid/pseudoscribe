"""Style analysis and adaptation API endpoints"""

from typing import Dict, List
import numpy as np

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from pseudoscribe.api.dependencies import (
    get_style_adapter,
    get_style_checker,
    get_style_profiler,
)
from pseudoscribe.infrastructure.style_adapter import StyleAdapter
from pseudoscribe.infrastructure.style_checker import StyleChecker
from pseudoscribe.infrastructure.style_profiler import StyleProfiler

# --- Router --- #
router = APIRouter(prefix="/style", tags=["style"])

# --- Pydantic Models --- #
class StyleAnalysisRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to analyze")

class StyleProfileResponse(BaseModel):
    complexity: float
    formality: float
    tone: float
    readability: float

class StyleComparisonRequest(BaseModel):
    text1: str = Field(..., min_length=1, description="First text to compare")
    text2: str = Field(..., min_length=1, description="Second text to compare")

class StyleComparisonResponse(BaseModel):
    overall_similarity: float
    vector_similarity: float
    feature_similarity: float

class StyleAdaptationRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to adapt")
    target_style: StyleProfileResponse
    strength: float = Field(0.5, ge=0, le=1, description="Strength of adaptation")

class StyleAdaptationResponse(BaseModel):
    adapted_text: str
    original_profile: StyleProfileResponse
    adapted_profile: StyleProfileResponse

class StyleCheckRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to check")
    target_style: StyleProfileResponse

class StyleCheckResponse(BaseModel):
    consistency: float
    suggestions: List[str]

# --- API Endpoints --- #
@router.post("/analyze", response_model=StyleProfileResponse, summary="Analyze text style")
async def analyze_style(
    request: StyleAnalysisRequest,
    profiler: StyleProfiler = Depends(get_style_profiler),
):
    """Analyzes and returns the style profile of a given text."""
    return await profiler.analyze_text(request.text)

@router.post("/compare", response_model=StyleComparisonResponse, summary="Compare text styles")
async def compare_styles(
    request: StyleComparisonRequest,
    profiler: StyleProfiler = Depends(get_style_profiler),
):
    """Compares the styles of two texts and returns a similarity score."""
    # The profiler's public method for comparison requires full profiles.
    # We construct them here before comparing.
    vector1 = await profiler.model_manager.generate_vectors(request.text1)
    profile1 = profiler._create_style_profile(request.text1, vector1)
    
    vector2 = await profiler.model_manager.generate_vectors(request.text2)
    profile2 = profiler._create_style_profile(request.text2, vector2)

    similarity_scores = await profiler.compare_profiles(profile1, profile2)

    return {
        "overall_similarity": similarity_scores["overall"],
        "vector_similarity": similarity_scores["vector_similarity"],
        "feature_similarity": similarity_scores["characteristics_similarity"]
    }

@router.post("/adapt", response_model=StyleAdaptationResponse, summary="Adapt text style")
async def adapt_style(
    request: StyleAdaptationRequest,
    adapter: StyleAdapter = Depends(get_style_adapter),
    profiler: StyleProfiler = Depends(get_style_profiler),
):
    """Adapts a text to a target style with a given strength."""
    target_style_dict = request.target_style.model_dump()
    result = await adapter.adapt_text_to_characteristics(
        request.text, target_style_dict
    )

    original_profile = await profiler.analyze_text(result["original_text"])
    adapted_profile = await profiler.analyze_text(result["adapted_text"])

    return StyleAdaptationResponse(
        adapted_text=result["adapted_text"],
        original_profile=original_profile,
        adapted_profile=adapted_profile,
    )

@router.post("/check", response_model=StyleCheckResponse, summary="Check text style consistency")
async def check_style(
    request: StyleCheckRequest, 
    checker: StyleChecker = Depends(get_style_checker)
):
    """Checks a text against a target style and provides suggestions."""
    target_style_dict = request.target_style.model_dump()
    result = await checker.check_style_against_target_characteristics(request.text, target_style_dict)
    return StyleCheckResponse(
        consistency=result["overall_match"],
        suggestions=result["suggestions"]
    )
