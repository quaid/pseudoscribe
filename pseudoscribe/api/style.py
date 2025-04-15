"""Style analysis and adaptation API endpoints"""

from fastapi import APIRouter, HTTPException, Depends, Body
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from pseudoscribe.infrastructure.style_profiler import StyleProfiler
from pseudoscribe.infrastructure.style_adapter import StyleAdapter
from pseudoscribe.infrastructure.style_checker import StyleChecker
from pseudoscribe.infrastructure.model_manager import ModelManager

# Create router
router = APIRouter(
    prefix="/api/style",
    tags=["style"],
    responses={404: {"description": "Not found"}},
)

# Initialize dependencies
model_manager = ModelManager()
style_profiler = StyleProfiler(model_manager=model_manager)
style_checker = StyleChecker(style_profiler=style_profiler)
style_adapter = StyleAdapter(style_profiler=style_profiler, style_checker=style_checker, model_manager=model_manager)


class StyleAnalysisRequest(BaseModel):
    """Request model for style analysis"""
    text: str = Field(..., min_length=1, description="Text to analyze")
    tenant_id: Optional[str] = Field(None, description="Tenant ID for multi-tenant deployments")


class StyleProfileResponse(BaseModel):
    """Response model for style profile"""
    complexity: float = Field(..., description="Text complexity score (0-1)")
    formality: float = Field(..., description="Formality score (0-1)")
    tone: float = Field(..., description="Tone score (0-1, where 0 is negative, 1 is positive)")
    readability: float = Field(..., description="Readability score (0-1)")


class StyleComparisonRequest(BaseModel):
    """Request model for style comparison"""
    text1: str = Field(..., min_length=1, description="First text sample")
    text2: str = Field(..., min_length=1, description="Second text sample")


class StyleComparisonResponse(BaseModel):
    """Response model for style comparison"""
    overall: float = Field(..., description="Overall similarity score (0-1)")
    vector_similarity: float = Field(..., description="Vector-based similarity (0-1)")
    characteristics_similarity: float = Field(..., description="Characteristic-based similarity (0-1)")
    profile1: StyleProfileResponse = Field(..., description="Style profile of first text")
    profile2: StyleProfileResponse = Field(..., description="Style profile of second text")


class StyleAdaptationRequest(BaseModel):
    """Request model for style adaptation"""
    text: str = Field(..., min_length=1, description="Text to adapt")
    target_style: Dict[str, float] = Field(..., description="Target style characteristics")
    strength: float = Field(0.5, ge=0.0, le=1.0, description="Adaptation strength (0-1)")


class StyleAdaptationResponse(BaseModel):
    """Response model for style adaptation"""
    original_text: str = Field(..., description="Original input text")
    adapted_text: str = Field(..., description="Adapted text matching target style")
    original_profile: StyleProfileResponse = Field(..., description="Style profile of original text")
    adapted_profile: StyleProfileResponse = Field(..., description="Style profile of adapted text")
    similarity: float = Field(..., description="Similarity between original and adapted text (0-1)")


@router.post("/analyze", response_model=StyleProfileResponse)
async def analyze_style(request: StyleAnalysisRequest):
    """
    Analyze the style of a text sample and return a style profile.
    
    The profile includes metrics for complexity, formality, tone, and readability.
    Each metric is normalized to a value between 0 and 1.
    """
    try:
        profile = await style_profiler.analyze_text(request.text)
        return StyleProfileResponse(**profile)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Style analysis failed: {str(e)}")


@router.post("/compare", response_model=StyleComparisonResponse)
async def compare_styles(request: StyleComparisonRequest):
    """
    Compare the styles of two text samples and return similarity metrics.
    
    This endpoint analyzes both texts and returns:
    - Overall similarity score
    - Vector-based similarity (semantic similarity)
    - Characteristic-based similarity (style feature similarity)
    - Style profiles for both texts
    """
    try:
        # Analyze both texts
        profile1_chars = await style_profiler.analyze_text(request.text1)
        profile2_chars = await style_profiler.analyze_text(request.text2)
        
        # Create full profiles for comparison
        vector1 = await model_manager.generate_vector(request.text1)
        vector2 = await model_manager.generate_vector(request.text2)
        
        profile1 = style_profiler._create_style_profile(request.text1, vector1)
        profile2 = style_profiler._create_style_profile(request.text2, vector2)
        
        # Compare profiles
        similarity = await style_profiler.compare_profiles(profile1, profile2)
        
        return StyleComparisonResponse(
            overall=similarity["overall"],
            vector_similarity=similarity["vector_similarity"],
            characteristics_similarity=similarity["characteristics_similarity"],
            profile1=StyleProfileResponse(**profile1_chars),
            profile2=StyleProfileResponse(**profile2_chars)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Style comparison failed: {str(e)}")


@router.post("/adapt", response_model=StyleAdaptationResponse)
async def adapt_style(request: StyleAdaptationRequest):
    """
    Adapt text to match a target style.
    
    This endpoint takes a text sample and adapts it to match the provided target style
    characteristics. The strength parameter controls how aggressively the adaptation
    is applied (0.0 = minimal changes, 1.0 = maximum adaptation).
    """
    try:
        # Analyze original text
        original_profile = await style_profiler.analyze_text(request.text)
        
        # Adapt text to target style
        adapted_text = await style_adapter.adapt_text(
            request.text, 
            request.target_style,
            strength=request.strength
        )
        
        # Analyze adapted text
        adapted_profile = await style_profiler.analyze_text(adapted_text)
        
        # Calculate similarity between original and adapted text
        vector1 = await model_manager.generate_vector(request.text)
        vector2 = await model_manager.generate_vector(adapted_text)
        
        profile1 = style_profiler._create_style_profile(request.text, vector1)
        profile2 = style_profiler._create_style_profile(adapted_text, vector2)
        
        similarity = await style_profiler.compare_profiles(profile1, profile2)
        
        return StyleAdaptationResponse(
            original_text=request.text,
            adapted_text=adapted_text,
            original_profile=StyleProfileResponse(**original_profile),
            adapted_profile=StyleProfileResponse(**adapted_profile),
            similarity=similarity["overall"]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Style adaptation failed: {str(e)}")


@router.post("/check", response_model=Dict[str, Any])
async def check_style(
    text: str = Body(..., embed=True),
    target_style: Optional[Dict[str, float]] = Body(None, embed=True),
    profile_id: Optional[str] = Body(None, embed=True)
):
    """
    Check if a text matches a target style and provide improvement suggestions.
    
    This endpoint compares the text's style against either:
    1. A provided target style object
    2. A stored style profile referenced by ID
    
    It returns style consistency metrics and suggestions for improvement.
    """
    try:
        if not target_style and not profile_id:
            raise HTTPException(
                status_code=400, 
                detail="Either target_style or profile_id must be provided"
            )
            
        # Get target style from profile if profile_id is provided
        if profile_id:
            profile = await style_profiler.retrieve_profile(profile_id)
            if not profile:
                raise HTTPException(status_code=404, detail=f"Style profile not found: {profile_id}")
            target_style = profile["characteristics"]
            
        # Check style consistency
        check_result = await style_checker.check_consistency(text, target_style)
        
        return check_result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Style check failed: {str(e)}")
