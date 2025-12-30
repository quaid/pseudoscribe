"""Multi-format output generator for PseudoScribe

This module provides functionality to generate content in various formats:
- Blog posts with structured sections
- Whitepapers with formal structure
- Social media posts (Twitter, LinkedIn)

Each format has specific templates and style adaptations to ensure
the generated content matches platform requirements and best practices.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from pseudoscribe.infrastructure.ollama_service import OllamaService


class OutputFormat(str, Enum):
    """Supported output formats"""
    BLOG_POST = "blog_post"
    WHITEPAPER = "whitepaper"
    SOCIAL_TWITTER = "social_twitter"
    SOCIAL_LINKEDIN = "social_linkedin"


class Section(BaseModel):
    """A section of content with heading and body"""
    heading: str = Field(..., description="Section heading")
    content: str = Field(..., description="Section content")


class BlogPostOutput(BaseModel):
    """Blog post output structure"""
    title: str = Field(..., description="Blog post title")
    sections: List[Section] = Field(..., description="Blog sections including intro and conclusion")
    meta_description: Optional[str] = Field(None, description="SEO meta description")
    keywords: Optional[List[str]] = Field(None, description="SEO keywords")


class WhitepaperOutput(BaseModel):
    """Whitepaper output structure"""
    title: str = Field(..., description="Whitepaper title")
    executive_summary: str = Field(..., description="Executive summary")
    sections: List[Section] = Field(..., description="Whitepaper sections")
    citations: Optional[List[str]] = Field(None, description="Citations and references")


class SocialMediaOutput(BaseModel):
    """Social media output structure"""
    platform: str = Field(..., description="Social media platform")
    content: str = Field(..., description="Post content")
    hashtags: Optional[List[str]] = Field(None, description="Hashtags")
    character_count: int = Field(..., description="Character count")


class GenerationRequest(BaseModel):
    """Request for content generation"""
    topic: str = Field(..., min_length=1, description="Topic to generate content about")
    format: OutputFormat = Field(..., description="Output format")
    target_length: Optional[int] = Field(None, gt=0, description="Target word count")
    max_length: Optional[int] = Field(None, gt=0, description="Maximum word count")
    style_params: Optional[Dict[str, Any]] = Field(None, description="Style parameters")
    keywords: Optional[List[str]] = Field(None, description="Keywords to include")
    include_citations: Optional[bool] = Field(False, description="Include citations")

    @field_validator("topic")
    @classmethod
    def validate_topic(cls, v: str) -> str:
        """Validate topic is not empty"""
        if not v or not v.strip():
            raise ValueError("Topic cannot be empty")
        return v.strip()

    @field_validator("target_length")
    @classmethod
    def validate_target_length(cls, v: Optional[int]) -> Optional[int]:
        """Validate target length is positive"""
        if v is not None and v <= 0:
            raise ValueError("Target length must be positive")
        return v

    @field_validator("max_length")
    @classmethod
    def validate_max_length(cls, v: Optional[int]) -> Optional[int]:
        """Validate max length is positive"""
        if v is not None and v <= 0:
            raise ValueError("Max length must be positive")
        return v


class OutputGenerator:
    """Generator for multi-format content output

    Uses OllamaService to generate content adapted to specific formats
    with appropriate structure, style, and length constraints.

    Supported formats:
    - Blog posts: Structured with introduction, body sections, and conclusion
    - Whitepapers: Formal documents with executive summary and citations
    - Social media: Twitter (280 chars) and LinkedIn (3000 chars) posts
    """

    # Platform character limits
    TWITTER_CHAR_LIMIT = 280
    LINKEDIN_CHAR_LIMIT = 3000

    # Default content parameters
    DEFAULT_BLOG_LENGTH = 500
    DEFAULT_MODEL = "llama2"

    def __init__(self, ollama_service: OllamaService):
        """Initialize the output generator

        Args:
            ollama_service: OllamaService instance for LLM operations
        """
        self.ollama_service = ollama_service
        self.default_model = self.DEFAULT_MODEL

    async def generate(self, request: GenerationRequest) -> Any:
        """Generate content in the requested format

        Routes to the appropriate generation method based on format.

        Args:
            request: Generation request with format and parameters

        Returns:
            Format-specific output (BlogPostOutput, WhitepaperOutput, or SocialMediaOutput)

        Raises:
            ValueError: If format is not supported
        """
        if request.format == OutputFormat.BLOG_POST:
            return await self.generate_blog_post(request)
        elif request.format == OutputFormat.WHITEPAPER:
            return await self.generate_whitepaper(request)
        elif request.format in [OutputFormat.SOCIAL_TWITTER, OutputFormat.SOCIAL_LINKEDIN]:
            return await self.generate_social(request)
        else:
            raise ValueError(f"Unsupported format: {request.format}")

    async def generate_blog_post(self, request: GenerationRequest) -> BlogPostOutput:
        """Generate a blog post with structured sections

        Creates a blog post with:
        - Engaging title
        - Introduction section
        - Body sections with subtopics
        - Conclusion section
        - SEO optimization with keywords

        Args:
            request: Generation request

        Returns:
            BlogPostOutput with structured sections
        """
        # Build prompt for blog post generation
        prompt = self._build_blog_post_prompt(request)

        # Generate content using Ollama
        response = await self.ollama_service.generate(
            model_name=self.default_model,
            prompt=prompt
        )

        # Parse the response into structured sections
        return self._parse_blog_post(response.response, request)

    def _build_blog_post_prompt(self, request: GenerationRequest) -> str:
        """Build the prompt for blog post generation"""
        # Build style context
        style_context = self._build_style_context(request.style_params)

        # Build keywords context
        keywords_context = ""
        if request.keywords:
            keywords_context = f"\nInclude these keywords naturally: {', '.join(request.keywords)}"

        # Determine target length
        target_words = request.target_length or self.DEFAULT_BLOG_LENGTH
        max_words = request.max_length or target_words + 200

        # Build prompt for blog post
        return f"""Write a blog post about: {request.topic}

{style_context}
Target length: approximately {target_words} words (maximum {max_words} words)
{keywords_context}

Format the blog post with:
- A catchy title on the first line starting with #
- An Introduction section (## Introduction)
- 2-3 body sections with descriptive headings (## Section Name)
- A Conclusion section (## Conclusion)

Write in markdown format with clear section headers."""

    async def generate_whitepaper(self, request: GenerationRequest) -> WhitepaperOutput:
        """Generate a formal whitepaper

        Creates a whitepaper with:
        - Formal title
        - Executive summary
        - Introduction
        - Body sections with analysis
        - Conclusion
        - Optional citations

        Args:
            request: Generation request

        Returns:
            WhitepaperOutput with formal structure
        """
        # Whitepapers are always formal and professional
        style_params = request.style_params or {}
        style_params.setdefault("formality", 0.95)
        style_params.setdefault("tone", "professional")

        style_context = self._build_style_context(style_params)

        # Build citations context
        citations_context = ""
        if request.include_citations:
            citations_context = "\nInclude a References section at the end with citations."

        # Build prompt for whitepaper
        prompt = f"""Write a formal whitepaper about: {request.topic}

{style_context}
Use a formal, technical, and professional tone suitable for business or academic audiences.
{citations_context}

Format the whitepaper with:
- A professional title on the first line starting with #
- An Executive Summary section (## Executive Summary) - brief overview
- An Introduction section (## Introduction)
- 2-3 analytical body sections with descriptive headings (## Section Name)
- A Conclusion section (## Conclusion)
{"- A References section (## References)" if request.include_citations else ""}

Write in markdown format with clear section headers."""

        # Generate content using Ollama
        response = await self.ollama_service.generate(
            model_name=self.default_model,
            prompt=prompt
        )

        # Parse the response into structured whitepaper
        return self._parse_whitepaper(response.response, request)

    async def generate_social(self, request: GenerationRequest) -> SocialMediaOutput:
        """Generate social media content

        Creates platform-specific content:
        - Twitter: Max 280 characters, hashtags, concise
        - LinkedIn: Max 3000 characters, professional, longer

        Args:
            request: Generation request

        Returns:
            SocialMediaOutput with platform-appropriate content
        """
        if request.format == OutputFormat.SOCIAL_TWITTER:
            return await self._generate_twitter(request)
        elif request.format == OutputFormat.SOCIAL_LINKEDIN:
            return await self._generate_linkedin(request)
        else:
            raise ValueError(f"Unsupported social format: {request.format}")

    async def _generate_twitter(self, request: GenerationRequest) -> SocialMediaOutput:
        """Generate Twitter post (max 280 characters)"""
        # Build keywords/hashtags
        hashtags_hint = ""
        if request.keywords:
            hashtags = ["#" + kw.replace(" ", "") for kw in request.keywords[:3]]
            hashtags_hint = f"\nInclude these hashtags: {' '.join(hashtags)}"

        prompt = f"""Write a Twitter post about: {request.topic}

Requirements:
- Maximum {self.TWITTER_CHAR_LIMIT} characters (STRICT LIMIT)
- Engaging and concise
- Include 1-3 relevant hashtags
{hashtags_hint}

Write only the tweet content, nothing else."""

        # Generate content
        response = await self.ollama_service.generate(
            model_name=self.default_model,
            prompt=prompt
        )

        # Ensure character limit
        content = response.response.strip()
        content = self._truncate_to_limit(content, self.TWITTER_CHAR_LIMIT)

        # Extract hashtags
        hashtags = self._extract_hashtags(content)

        return SocialMediaOutput(
            platform="twitter",
            content=content,
            hashtags=hashtags if hashtags else None,
            character_count=len(content)
        )

    async def _generate_linkedin(self, request: GenerationRequest) -> SocialMediaOutput:
        """Generate LinkedIn post (max 3000 characters)"""
        # LinkedIn is professional
        style_params = request.style_params or {}
        style_params.setdefault("tone", "professional")

        style_context = self._build_style_context(style_params)

        # Build hashtags hint
        hashtags_hint = ""
        if request.keywords:
            hashtags = ["#" + kw.replace(" ", "") for kw in request.keywords[:5]]
            hashtags_hint = f"\nInclude these hashtags at the end: {' '.join(hashtags)}"

        prompt = f"""Write a LinkedIn post about: {request.topic}

{style_context}
Requirements:
- Professional and business-appropriate tone
- Maximum {self.LINKEDIN_CHAR_LIMIT} characters
- Engaging for professional audience
- Use line breaks for readability
- Can use bullet points or emojis sparingly
{hashtags_hint}

Write only the LinkedIn post content."""

        # Generate content
        response = await self.ollama_service.generate(
            model_name=self.default_model,
            prompt=prompt
        )

        # Ensure character limit
        content = response.response.strip()
        content = self._truncate_to_limit(content, self.LINKEDIN_CHAR_LIMIT)

        # Extract hashtags
        hashtags = self._extract_hashtags(content)

        return SocialMediaOutput(
            platform="linkedin",
            content=content,
            hashtags=hashtags if hashtags else None,
            character_count=len(content)
        )

    def _extract_hashtags(self, content: str) -> List[str]:
        """Extract hashtags from content

        Args:
            content: Text content to extract hashtags from

        Returns:
            List of hashtags found in content
        """
        return [word for word in content.split() if word.startswith("#")]

    def _build_style_context(self, style_params: Optional[Dict[str, Any]]) -> str:
        """Build style context string from parameters"""
        if not style_params:
            return ""

        context_parts = []

        # Formality
        if "formality" in style_params:
            formality = style_params["formality"]
            if formality >= 0.8:
                context_parts.append("Use a very formal and professional tone.")
            elif formality >= 0.5:
                context_parts.append("Use a balanced, professional tone.")
            else:
                context_parts.append("Use a casual and conversational tone.")

        # Tone
        if "tone" in style_params:
            tone = style_params["tone"]
            context_parts.append(f"Tone should be {tone}.")

        return "\n".join(context_parts) if context_parts else ""

    def _parse_blog_post(self, content: str, request: GenerationRequest) -> BlogPostOutput:
        """Parse generated content into BlogPostOutput structure"""
        lines = content.split("\n")

        # Extract title (first line with #)
        title = "Untitled"
        for line in lines:
            if line.strip().startswith("# "):
                title = line.strip()[2:].strip()
                break

        # Extract sections
        sections = []
        current_heading = None
        current_content = []

        for line in lines:
            if line.strip().startswith("## "):
                # Save previous section
                if current_heading:
                    sections.append(Section(
                        heading=current_heading,
                        content="\n".join(current_content).strip()
                    ))
                # Start new section
                current_heading = line.strip()[3:].strip()
                current_content = []
            elif current_heading and line.strip():
                current_content.append(line.strip())

        # Save last section
        if current_heading:
            sections.append(Section(
                heading=current_heading,
                content="\n".join(current_content).strip()
            ))

        # Ensure we have at least intro and conclusion
        if not any("introduction" in s.heading.lower() for s in sections):
            sections.insert(0, Section(heading="Introduction", content="Introduction content"))
        if not any("conclusion" in s.heading.lower() for s in sections):
            sections.append(Section(heading="Conclusion", content="Conclusion content"))

        # Truncate if needed
        if request.max_length:
            sections = self._truncate_sections(sections, request.max_length)

        return BlogPostOutput(
            title=title,
            sections=sections,
            keywords=request.keywords
        )

    def _parse_whitepaper(self, content: str, request: GenerationRequest) -> WhitepaperOutput:
        """Parse generated content into WhitepaperOutput structure"""
        lines = content.split("\n")

        # Extract title
        title = "Untitled Whitepaper"
        for line in lines:
            if line.strip().startswith("# "):
                title = line.strip()[2:].strip()
                break

        # Extract executive summary and sections
        executive_summary = ""
        sections = []
        citations = []
        current_heading = None
        current_content = []

        for line in lines:
            if line.strip().startswith("## "):
                # Save previous section
                if current_heading:
                    content_text = "\n".join(current_content).strip()

                    if "executive summary" in current_heading.lower():
                        executive_summary = content_text
                    elif "reference" in current_heading.lower() or "citation" in current_heading.lower():
                        citations = [c.strip() for c in content_text.split("\n") if c.strip()]
                    else:
                        sections.append(Section(
                            heading=current_heading,
                            content=content_text
                        ))

                # Start new section
                current_heading = line.strip()[3:].strip()
                current_content = []
            elif current_heading and line.strip():
                current_content.append(line.strip())

        # Save last section
        if current_heading:
            content_text = "\n".join(current_content).strip()
            if "executive summary" in current_heading.lower():
                executive_summary = content_text
            elif "reference" in current_heading.lower() or "citation" in current_heading.lower():
                citations = [c.strip() for c in content_text.split("\n") if c.strip()]
            else:
                sections.append(Section(
                    heading=current_heading,
                    content=content_text
                ))

        # Default executive summary if not found
        if not executive_summary:
            executive_summary = "Executive summary not generated."

        return WhitepaperOutput(
            title=title,
            executive_summary=executive_summary,
            sections=sections,
            citations=citations if citations else None
        )

    def _truncate_sections(self, sections: List[Section], max_words: int) -> List[Section]:
        """Truncate sections to fit within max word count"""
        total_words = sum(len(s.content.split()) for s in sections)

        if total_words <= max_words:
            return sections

        # Proportionally reduce each section
        ratio = max_words / total_words
        truncated = []

        for section in sections:
            words = section.content.split()
            target_words = int(len(words) * ratio)
            if target_words > 0:
                truncated_content = " ".join(words[:target_words])
                truncated.append(Section(
                    heading=section.heading,
                    content=truncated_content
                ))

        return truncated

    def _truncate_to_limit(self, text: str, max_chars: int) -> str:
        """Truncate text to character limit, preserving word boundaries"""
        if len(text) <= max_chars:
            return text

        # Find last space before limit
        truncated = text[:max_chars]
        last_space = truncated.rfind(" ")

        if last_space > 0:
            return truncated[:last_space].strip()

        return truncated.strip()
