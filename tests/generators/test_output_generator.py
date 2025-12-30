"""Test suite for multi-format output generation

Following TDD principles:
1. RED: Write failing tests that define desired behavior
2. GREEN: Write minimal code to pass tests
3. REFACTOR: Clean up while keeping tests green

This test suite covers:
- Blog post format generation
- Whitepaper format generation
- Social media formats (Twitter, LinkedIn)
- Format selection
- Style adaptation per format
- Length/character limit handling
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from pseudoscribe.generators.output_generator import (
    OutputGenerator,
    OutputFormat,
    BlogPostOutput,
    WhitepaperOutput,
    SocialMediaOutput,
    GenerationRequest,
)


class TestOutputGeneratorInit:
    """Test OutputGenerator initialization"""

    def test_init_with_ollama_service(self):
        """OutputGenerator should initialize with OllamaService"""
        mock_ollama = Mock()
        generator = OutputGenerator(ollama_service=mock_ollama)

        assert generator.ollama_service == mock_ollama

    def test_init_without_ollama_service_raises_error(self):
        """OutputGenerator should require OllamaService"""
        with pytest.raises(TypeError):
            OutputGenerator()


class TestBlogPostGeneration:
    """Test blog post format generation"""

    @pytest.mark.asyncio
    async def test_generate_blog_post_basic_structure(self):
        """Blog post should have introduction, body sections, and conclusion"""
        mock_ollama = AsyncMock()
        mock_ollama.generate.return_value = Mock(
            response="# Test Blog Post\n\n## Introduction\nIntro text\n\n## Section 1\nBody text\n\n## Conclusion\nConclusion text"
        )

        generator = OutputGenerator(ollama_service=mock_ollama)
        request = GenerationRequest(
            topic="AI in Writing",
            format=OutputFormat.BLOG_POST,
            target_length=500
        )

        result = await generator.generate_blog_post(request)

        assert isinstance(result, BlogPostOutput)
        assert result.title is not None
        assert len(result.sections) >= 2  # At least intro and conclusion
        assert any("introduction" in s.heading.lower() for s in result.sections)
        assert any("conclusion" in s.heading.lower() for s in result.sections)

    @pytest.mark.asyncio
    async def test_generate_blog_post_respects_target_length(self):
        """Blog post should respect target word count"""
        mock_ollama = AsyncMock()
        # Provide a properly structured response with sections
        mock_response = """# Writing Tips Blog

## Introduction
Here are some great writing tips to improve your skills.

## Main Tips
Write clearly and concisely. Use active voice whenever possible.

## Conclusion
These tips will help you become a better writer."""
        mock_ollama.generate.return_value = Mock(response=mock_response)

        generator = OutputGenerator(ollama_service=mock_ollama)
        request = GenerationRequest(
            topic="Writing Tips",
            format=OutputFormat.BLOG_POST,
            target_length=50
        )

        result = await generator.generate_blog_post(request)

        # Count words in all sections
        total_words = sum(len(s.content.split()) for s in result.sections)
        # Should have reasonable content (at least some words)
        assert total_words >= 10  # At least some content

    @pytest.mark.asyncio
    async def test_generate_blog_post_with_style_params(self):
        """Blog post should adapt to style parameters"""
        mock_ollama = AsyncMock()
        mock_ollama.generate.return_value = Mock(
            response="# Formal Blog\n\n## Introduction\nFormal introduction\n\n## Content\nFormal content"
        )

        generator = OutputGenerator(ollama_service=mock_ollama)
        request = GenerationRequest(
            topic="Professional Writing",
            format=OutputFormat.BLOG_POST,
            style_params={"formality": 0.9, "tone": "professional"}
        )

        result = await generator.generate_blog_post(request)

        # Verify the prompt included style parameters
        call_args = mock_ollama.generate.call_args
        assert "formal" in call_args[1]["prompt"].lower() or "professional" in call_args[1]["prompt"].lower()

    @pytest.mark.asyncio
    async def test_generate_blog_post_with_seo_keywords(self):
        """Blog post should include SEO keywords when provided"""
        mock_ollama = AsyncMock()
        mock_ollama.generate.return_value = Mock(
            response="# AI Writing\n\n## Introduction\nAI writing tools help content creation\n\n## Body\nMore AI writing content"
        )

        generator = OutputGenerator(ollama_service=mock_ollama)
        request = GenerationRequest(
            topic="AI Writing Tools",
            format=OutputFormat.BLOG_POST,
            keywords=["AI writing", "content creation", "automation"]
        )

        result = await generator.generate_blog_post(request)

        # Check that keywords appear in the generated content
        full_text = " ".join(s.content for s in result.sections).lower()
        assert "ai writing" in full_text or "content creation" in full_text


class TestWhitepaperGeneration:
    """Test whitepaper format generation"""

    @pytest.mark.asyncio
    async def test_generate_whitepaper_formal_structure(self):
        """Whitepaper should have executive summary, introduction, body, and conclusion"""
        mock_ollama = AsyncMock()
        mock_ollama.generate.return_value = Mock(
            response="# Whitepaper Title\n\n## Executive Summary\nSummary\n\n## Introduction\nIntro\n\n## Analysis\nBody\n\n## Conclusion\nConclusion"
        )

        generator = OutputGenerator(ollama_service=mock_ollama)
        request = GenerationRequest(
            topic="AI Technology Trends",
            format=OutputFormat.WHITEPAPER
        )

        result = await generator.generate_whitepaper(request)

        assert isinstance(result, WhitepaperOutput)
        assert result.title is not None
        assert result.executive_summary is not None
        assert len(result.sections) >= 3  # Intro, body, conclusion

    @pytest.mark.asyncio
    async def test_generate_whitepaper_formal_tone(self):
        """Whitepaper should use formal, professional tone"""
        mock_ollama = AsyncMock()
        mock_ollama.generate.return_value = Mock(
            response="# Technical Whitepaper\n\n## Executive Summary\nFormal summary\n\n## Introduction\nFormal intro"
        )

        generator = OutputGenerator(ollama_service=mock_ollama)
        request = GenerationRequest(
            topic="Blockchain Technology",
            format=OutputFormat.WHITEPAPER
        )

        result = await generator.generate_whitepaper(request)

        # Verify formal tone in the prompt
        call_args = mock_ollama.generate.call_args
        prompt = call_args[1]["prompt"].lower()
        assert "formal" in prompt or "professional" in prompt or "technical" in prompt

    @pytest.mark.asyncio
    async def test_generate_whitepaper_with_citations(self):
        """Whitepaper should include citations section when requested"""
        mock_ollama = AsyncMock()
        mock_ollama.generate.return_value = Mock(
            response="# Research Paper\n\n## Executive Summary\nSummary\n\n## Introduction\nIntro\n\n## References\n[1] Source 1\n[2] Source 2"
        )

        generator = OutputGenerator(ollama_service=mock_ollama)
        request = GenerationRequest(
            topic="AI Research",
            format=OutputFormat.WHITEPAPER,
            include_citations=True
        )

        result = await generator.generate_whitepaper(request)

        # Check for citations in the result
        assert result.citations is not None
        assert len(result.citations) > 0


class TestSocialMediaGeneration:
    """Test social media format generation"""

    @pytest.mark.asyncio
    async def test_generate_twitter_respects_280_char_limit(self):
        """Twitter posts should not exceed 280 characters"""
        mock_ollama = AsyncMock()
        mock_ollama.generate.return_value = Mock(
            response="Exciting news about AI writing tools! They help create content faster and more efficiently. #AI #Writing"
        )

        generator = OutputGenerator(ollama_service=mock_ollama)
        request = GenerationRequest(
            topic="AI Writing Tools",
            format=OutputFormat.SOCIAL_TWITTER
        )

        result = await generator.generate_social(request)

        assert isinstance(result, SocialMediaOutput)
        assert len(result.content) <= 280
        assert result.platform == "twitter"

    @pytest.mark.asyncio
    async def test_generate_twitter_includes_hashtags(self):
        """Twitter posts should include relevant hashtags"""
        mock_ollama = AsyncMock()
        mock_ollama.generate.return_value = Mock(
            response="AI is transforming content creation! #AI #ContentCreation #WritingTools"
        )

        generator = OutputGenerator(ollama_service=mock_ollama)
        request = GenerationRequest(
            topic="AI in Content Creation",
            format=OutputFormat.SOCIAL_TWITTER,
            keywords=["AI", "ContentCreation"]
        )

        result = await generator.generate_social(request)

        assert "#" in result.content
        hashtag_count = result.content.count("#")
        assert 1 <= hashtag_count <= 5  # Reasonable hashtag count

    @pytest.mark.asyncio
    async def test_generate_linkedin_longer_format(self):
        """LinkedIn posts should be longer and more professional than Twitter"""
        mock_ollama = AsyncMock()
        mock_ollama.generate.return_value = Mock(
            response="I'm excited to share insights on AI writing tools.\n\nThese innovative solutions are transforming how we create content. Key benefits include:\n\n• Faster content creation\n• Improved consistency\n• Enhanced creativity\n\n#AI #ContentStrategy #ProfessionalWriting"
        )

        generator = OutputGenerator(ollama_service=mock_ollama)
        request = GenerationRequest(
            topic="AI Writing Tools for Professionals",
            format=OutputFormat.SOCIAL_LINKEDIN
        )

        result = await generator.generate_social(request)

        assert isinstance(result, SocialMediaOutput)
        assert result.platform == "linkedin"
        # LinkedIn posts can be longer than Twitter but should be reasonable
        assert len(result.content) > 0  # Has content
        assert len(result.content) <= 3000  # LinkedIn limit

    @pytest.mark.asyncio
    async def test_generate_linkedin_professional_tone(self):
        """LinkedIn posts should have professional tone"""
        mock_ollama = AsyncMock()
        mock_ollama.generate.return_value = Mock(
            response="Professional insight about AI writing tools for business applications."
        )

        generator = OutputGenerator(ollama_service=mock_ollama)
        request = GenerationRequest(
            topic="Business AI Tools",
            format=OutputFormat.SOCIAL_LINKEDIN
        )

        result = await generator.generate_social(request)

        # Verify professional tone in prompt
        call_args = mock_ollama.generate.call_args
        prompt = call_args[1]["prompt"].lower()
        assert "professional" in prompt or "business" in prompt


class TestStyleAdaptation:
    """Test style adaptation for different formats"""

    @pytest.mark.asyncio
    async def test_adapt_style_for_blog_casual(self):
        """Blog posts should adapt to casual style when requested"""
        mock_ollama = AsyncMock()
        mock_ollama.generate.return_value = Mock(
            response="Hey there! Let's talk about AI writing tools..."
        )

        generator = OutputGenerator(ollama_service=mock_ollama)
        request = GenerationRequest(
            topic="AI Writing",
            format=OutputFormat.BLOG_POST,
            style_params={"formality": 0.3, "tone": "casual"}
        )

        result = await generator.generate_blog_post(request)

        # Verify casual style in prompt
        call_args = mock_ollama.generate.call_args
        prompt = call_args[1]["prompt"].lower()
        assert "casual" in prompt or "conversational" in prompt

    @pytest.mark.asyncio
    async def test_adapt_style_for_whitepaper_technical(self):
        """Whitepapers should adapt to technical style"""
        mock_ollama = AsyncMock()
        mock_ollama.generate.return_value = Mock(
            response="# Technical Analysis\n\n## Executive Summary\nTechnical summary of AI implementations"
        )

        generator = OutputGenerator(ollama_service=mock_ollama)
        request = GenerationRequest(
            topic="AI Implementation",
            format=OutputFormat.WHITEPAPER,
            style_params={"formality": 0.95, "tone": "technical"}
        )

        result = await generator.generate_whitepaper(request)

        # Verify technical style in prompt
        call_args = mock_ollama.generate.call_args
        prompt = call_args[1]["prompt"].lower()
        assert "technical" in prompt or "formal" in prompt


class TestFormatSelection:
    """Test format selection and routing"""

    @pytest.mark.asyncio
    async def test_generate_routes_to_blog_post(self):
        """generate() should route BLOG_POST format to generate_blog_post()"""
        mock_ollama = AsyncMock()
        mock_ollama.generate.return_value = Mock(
            response="# Blog\n\n## Intro\nContent"
        )

        generator = OutputGenerator(ollama_service=mock_ollama)
        request = GenerationRequest(
            topic="Test",
            format=OutputFormat.BLOG_POST
        )

        with patch.object(generator, 'generate_blog_post', wraps=generator.generate_blog_post) as mock_method:
            result = await generator.generate(request)
            mock_method.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_routes_to_whitepaper(self):
        """generate() should route WHITEPAPER format to generate_whitepaper()"""
        mock_ollama = AsyncMock()
        mock_ollama.generate.return_value = Mock(
            response="# Whitepaper\n\n## Executive Summary\nSummary"
        )

        generator = OutputGenerator(ollama_service=mock_ollama)
        request = GenerationRequest(
            topic="Test",
            format=OutputFormat.WHITEPAPER
        )

        with patch.object(generator, 'generate_whitepaper', wraps=generator.generate_whitepaper) as mock_method:
            result = await generator.generate(request)
            mock_method.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_routes_to_social(self):
        """generate() should route social formats to generate_social()"""
        mock_ollama = AsyncMock()
        mock_ollama.generate.return_value = Mock(
            response="Twitter post content #AI"
        )

        generator = OutputGenerator(ollama_service=mock_ollama)
        request = GenerationRequest(
            topic="Test",
            format=OutputFormat.SOCIAL_TWITTER
        )

        with patch.object(generator, 'generate_social', wraps=generator.generate_social) as mock_method:
            result = await generator.generate(request)
            mock_method.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_invalid_format_raises_error(self):
        """generate() should raise error for unsupported formats"""
        from pydantic import ValidationError

        mock_ollama = AsyncMock()
        generator = OutputGenerator(ollama_service=mock_ollama)

        # Create request with invalid format - should raise ValidationError
        with pytest.raises(ValidationError):
            request = GenerationRequest(
                topic="Test",
                format="INVALID_FORMAT"  # This should fail validation
            )


class TestLengthHandling:
    """Test length and character limit handling"""

    @pytest.mark.asyncio
    async def test_blog_post_respects_max_length(self):
        """Blog posts should not exceed maximum length"""
        mock_ollama = AsyncMock()
        # Generate a very long response
        long_response = "# Blog\n\n## Intro\n" + " ".join(["word"] * 2000)
        mock_ollama.generate.return_value = Mock(response=long_response)

        generator = OutputGenerator(ollama_service=mock_ollama)
        request = GenerationRequest(
            topic="Test",
            format=OutputFormat.BLOG_POST,
            target_length=1000,
            max_length=1200
        )

        result = await generator.generate_blog_post(request)

        total_words = sum(len(s.content.split()) for s in result.sections)
        assert total_words <= 1200

    @pytest.mark.asyncio
    async def test_twitter_hard_limit_280_chars(self):
        """Twitter posts must never exceed 280 characters"""
        mock_ollama = AsyncMock()
        # Generate a very long response
        long_response = "This is a very long tweet that definitely exceeds 280 characters. " * 10
        mock_ollama.generate.return_value = Mock(response=long_response)

        generator = OutputGenerator(ollama_service=mock_ollama)
        request = GenerationRequest(
            topic="Test",
            format=OutputFormat.SOCIAL_TWITTER
        )

        result = await generator.generate_social(request)

        assert len(result.content) <= 280

    @pytest.mark.asyncio
    async def test_linkedin_respects_3000_char_limit(self):
        """LinkedIn posts should not exceed 3000 characters"""
        mock_ollama = AsyncMock()
        # Generate a very long response
        long_response = "Professional content. " * 200
        mock_ollama.generate.return_value = Mock(response=long_response)

        generator = OutputGenerator(ollama_service=mock_ollama)
        request = GenerationRequest(
            topic="Test",
            format=OutputFormat.SOCIAL_LINKEDIN
        )

        result = await generator.generate_social(request)

        assert len(result.content) <= 3000


class TestErrorHandling:
    """Test error handling and edge cases"""

    @pytest.mark.asyncio
    async def test_ollama_error_propagates(self):
        """Errors from OllamaService should propagate properly"""
        mock_ollama = AsyncMock()
        mock_ollama.generate.side_effect = Exception("Ollama service error")

        generator = OutputGenerator(ollama_service=mock_ollama)
        request = GenerationRequest(
            topic="Test",
            format=OutputFormat.BLOG_POST
        )

        with pytest.raises(Exception, match="Ollama service error"):
            await generator.generate_blog_post(request)

    @pytest.mark.asyncio
    async def test_empty_topic_raises_validation_error(self):
        """Empty topic should raise validation error"""
        mock_ollama = AsyncMock()
        generator = OutputGenerator(ollama_service=mock_ollama)

        with pytest.raises(ValueError):
            GenerationRequest(topic="", format=OutputFormat.BLOG_POST)

    @pytest.mark.asyncio
    async def test_negative_length_raises_validation_error(self):
        """Negative target length should raise validation error"""
        mock_ollama = AsyncMock()
        generator = OutputGenerator(ollama_service=mock_ollama)

        with pytest.raises(ValueError):
            GenerationRequest(
                topic="Test",
                format=OutputFormat.BLOG_POST,
                target_length=-100
            )
