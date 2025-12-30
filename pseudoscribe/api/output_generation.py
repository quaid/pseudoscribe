"""Output generation API endpoints

Provides REST API endpoints for multi-format content generation:
- Blog posts
- Whitepapers
- Social media posts (Twitter, LinkedIn)
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from pseudoscribe.api.dependencies import get_ollama_service
from pseudoscribe.infrastructure.ollama_service import OllamaService
from pseudoscribe.generators.output_generator import (
    OutputGenerator,
    OutputFormat,
    GenerationRequest as GenRequest,
    BlogPostOutput,
    WhitepaperOutput,
    SocialMediaOutput,
)

# Router configuration
router = APIRouter(prefix="/api/v1/generate", tags=["output-generation"])


# --- Request/Response Models --- #

class BlogPostRequest(BaseModel):
    """Request model for blog post generation"""
    topic: str = Field(..., min_length=1, description="Topic to write about")
    target_length: Optional[int] = Field(None, gt=0, description="Target word count")
    max_length: Optional[int] = Field(None, gt=0, description="Maximum word count")
    keywords: Optional[List[str]] = Field(None, description="SEO keywords to include")
    formality: Optional[float] = Field(None, ge=0, le=1, description="Formality level (0=casual, 1=formal)")
    tone: Optional[str] = Field(None, description="Tone (e.g., 'professional', 'casual', 'friendly')")


class WhitepaperRequest(BaseModel):
    """Request model for whitepaper generation"""
    topic: str = Field(..., min_length=1, description="Topic to write about")
    include_citations: Optional[bool] = Field(False, description="Include references section")
    formality: Optional[float] = Field(0.95, ge=0, le=1, description="Formality level")


class SocialMediaRequest(BaseModel):
    """Request model for social media post generation"""
    topic: str = Field(..., min_length=1, description="Topic to write about")
    platform: str = Field(..., description="Platform: 'twitter' or 'linkedin'")
    keywords: Optional[List[str]] = Field(None, description="Keywords/hashtags to include")
    tone: Optional[str] = Field(None, description="Tone of the post")


class GenerateRequest(BaseModel):
    """Generic generation request with format selection"""
    topic: str = Field(..., min_length=1, description="Topic to write about")
    format: OutputFormat = Field(..., description="Output format")
    target_length: Optional[int] = Field(None, gt=0, description="Target length in words")
    max_length: Optional[int] = Field(None, gt=0, description="Maximum length in words")
    keywords: Optional[List[str]] = Field(None, description="Keywords to include")
    include_citations: Optional[bool] = Field(False, description="Include citations (for whitepapers)")
    formality: Optional[float] = Field(None, ge=0, le=1, description="Formality level")
    tone: Optional[str] = Field(None, description="Tone")


# --- Dependency Injection --- #

def get_output_generator(
    ollama_service: OllamaService = Depends(get_ollama_service)
) -> OutputGenerator:
    """Get OutputGenerator instance"""
    return OutputGenerator(ollama_service=ollama_service)


# --- API Endpoints --- #

@router.post("/blog", response_model=BlogPostOutput)
async def generate_blog_post(
    request: BlogPostRequest,
    generator: OutputGenerator = Depends(get_output_generator)
):
    """Generate a blog post

    Creates a structured blog post with introduction, body sections, and conclusion.
    Optimized for SEO with keyword integration.

    Args:
        request: Blog post generation parameters
        generator: OutputGenerator instance (injected)

    Returns:
        BlogPostOutput with structured sections

    Raises:
        HTTPException: If generation fails
    """
    try:
        # Build style parameters
        style_params = {}
        if request.formality is not None:
            style_params["formality"] = request.formality
        if request.tone is not None:
            style_params["tone"] = request.tone

        # Create generation request
        gen_request = GenRequest(
            topic=request.topic,
            format=OutputFormat.BLOG_POST,
            target_length=request.target_length,
            max_length=request.max_length,
            keywords=request.keywords,
            style_params=style_params if style_params else None
        )

        # Generate blog post
        result = await generator.generate_blog_post(gen_request)
        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate blog post: {str(e)}"
        )


@router.post("/whitepaper", response_model=WhitepaperOutput)
async def generate_whitepaper(
    request: WhitepaperRequest,
    generator: OutputGenerator = Depends(get_output_generator)
):
    """Generate a formal whitepaper

    Creates a professional whitepaper with executive summary, structured sections,
    and optional citations.

    Args:
        request: Whitepaper generation parameters
        generator: OutputGenerator instance (injected)

    Returns:
        WhitepaperOutput with formal structure

    Raises:
        HTTPException: If generation fails
    """
    try:
        # Build style parameters
        style_params = {
            "formality": request.formality,
            "tone": "professional"
        }

        # Create generation request
        gen_request = GenRequest(
            topic=request.topic,
            format=OutputFormat.WHITEPAPER,
            include_citations=request.include_citations,
            style_params=style_params
        )

        # Generate whitepaper
        result = await generator.generate_whitepaper(gen_request)
        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate whitepaper: {str(e)}"
        )


@router.post("/social", response_model=SocialMediaOutput)
async def generate_social_media(
    request: SocialMediaRequest,
    generator: OutputGenerator = Depends(get_output_generator)
):
    """Generate a social media post

    Creates platform-specific content:
    - Twitter: Max 280 characters with hashtags
    - LinkedIn: Professional post up to 3000 characters

    Args:
        request: Social media generation parameters
        generator: OutputGenerator instance (injected)

    Returns:
        SocialMediaOutput with platform-appropriate content

    Raises:
        HTTPException: If generation fails or platform is invalid
    """
    try:
        # Map platform to format
        if request.platform.lower() == "twitter":
            format_type = OutputFormat.SOCIAL_TWITTER
        elif request.platform.lower() == "linkedin":
            format_type = OutputFormat.SOCIAL_LINKEDIN
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported platform: {request.platform}. Use 'twitter' or 'linkedin'."
            )

        # Build style parameters
        style_params = {}
        if request.tone:
            style_params["tone"] = request.tone

        # Create generation request
        gen_request = GenRequest(
            topic=request.topic,
            format=format_type,
            keywords=request.keywords,
            style_params=style_params if style_params else None
        )

        # Generate social media post
        result = await generator.generate_social(gen_request)
        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate social media post: {str(e)}"
        )


@router.post("", response_model=BlogPostOutput | WhitepaperOutput | SocialMediaOutput)
async def generate_content(
    request: GenerateRequest,
    generator: OutputGenerator = Depends(get_output_generator)
):
    """Generate content in any supported format

    Generic endpoint that routes to the appropriate generator based on format.
    Supports blog posts, whitepapers, and social media formats.

    Args:
        request: Generic generation request with format selection
        generator: OutputGenerator instance (injected)

    Returns:
        Format-specific output (BlogPostOutput, WhitepaperOutput, or SocialMediaOutput)

    Raises:
        HTTPException: If generation fails
    """
    try:
        # Build style parameters
        style_params = {}
        if request.formality is not None:
            style_params["formality"] = request.formality
        if request.tone is not None:
            style_params["tone"] = request.tone

        # Create generation request
        gen_request = GenRequest(
            topic=request.topic,
            format=request.format,
            target_length=request.target_length,
            max_length=request.max_length,
            keywords=request.keywords,
            include_citations=request.include_citations,
            style_params=style_params if style_params else None
        )

        # Generate content using the appropriate method
        result = await generator.generate(gen_request)
        return result

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid request: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate content: {str(e)}"
        )
