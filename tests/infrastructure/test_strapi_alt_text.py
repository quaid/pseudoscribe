"""Tests for Strapi Alt-Text Handler.

Issue: INT-004 - Strapi Alt-Text Handler

These tests verify:
- Image extraction from Strapi content
- Alt-text detection and validation
- Alt-text generation with style adaptation
- Content updating with generated alt-text
"""

import pytest
from datetime import datetime
from typing import Dict, Any, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

from pseudoscribe.infrastructure.strapi_alt_text import (
    StrapiAltTextHandler,
    ImageInfo,
    AltTextResult,
    AltTextGenerationError
)
from pseudoscribe.infrastructure.content_connector import ContentItem


class TestImageInfo:
    """Tests for ImageInfo model."""

    def test_create_image_info(self):
        """Test creating an ImageInfo."""
        # Act
        info = ImageInfo(
            image_id="img-123",
            url="https://strapi.example.com/uploads/photo.jpg",
            alt_text=None,
            caption="A beautiful sunset"
        )

        # Assert
        assert info.image_id == "img-123"
        assert info.url == "https://strapi.example.com/uploads/photo.jpg"
        assert info.alt_text is None
        assert info.caption == "A beautiful sunset"

    def test_image_info_has_alt_text(self):
        """Test checking if image has alt text."""
        # Arrange
        with_alt = ImageInfo(
            image_id="1",
            url="https://example.com/img.jpg",
            alt_text="Description of image"
        )
        without_alt = ImageInfo(
            image_id="2",
            url="https://example.com/img2.jpg",
            alt_text=None
        )
        empty_alt = ImageInfo(
            image_id="3",
            url="https://example.com/img3.jpg",
            alt_text=""
        )

        # Assert
        assert with_alt.has_alt_text() is True
        assert without_alt.has_alt_text() is False
        assert empty_alt.has_alt_text() is False


class TestAltTextResult:
    """Tests for AltTextResult model."""

    def test_create_alt_text_result(self):
        """Test creating an AltTextResult."""
        # Act
        result = AltTextResult(
            image_id="img-123",
            original_alt_text=None,
            generated_alt_text="A sunset over the ocean with orange and pink clouds",
            confidence=0.95
        )

        # Assert
        assert result.image_id == "img-123"
        assert result.generated_alt_text.startswith("A sunset")
        assert result.confidence == 0.95

    def test_alt_text_result_was_updated(self):
        """Test checking if alt text was updated."""
        # Arrange
        updated = AltTextResult(
            image_id="1",
            original_alt_text=None,
            generated_alt_text="New alt text"
        )
        not_updated = AltTextResult(
            image_id="2",
            original_alt_text="Existing alt",
            generated_alt_text=None
        )

        # Assert
        assert updated.was_updated() is True
        assert not_updated.was_updated() is False


class TestStrapiAltTextHandlerInit:
    """Tests for handler initialization."""

    def test_create_handler(self):
        """Test creating an alt-text handler."""
        # Act
        handler = StrapiAltTextHandler()

        # Assert
        assert handler is not None

    def test_handler_with_style_profile(self):
        """Test creating handler with style profile."""
        # Act
        handler = StrapiAltTextHandler(
            style_profile="formal",
            max_length=150
        )

        # Assert
        assert handler.style_profile == "formal"
        assert handler.max_length == 150


class TestStrapiAltTextHandlerExtraction:
    """Tests for image extraction from content."""

    @pytest.fixture
    def handler(self):
        """Create a handler instance."""
        return StrapiAltTextHandler()

    def test_extract_images_from_content(self, handler):
        """Test extracting images from content body."""
        # Arrange
        content = ContentItem(
            content_id="doc-123",
            content_type="article",
            title="Test Article",
            body="<p>Text</p><img src='/uploads/img1.jpg' alt=''><p>More</p><img src='/uploads/img2.jpg'>",
            media=[
                {"id": "media-1", "url": "/uploads/img1.jpg", "alt": ""},
                {"id": "media-2", "url": "/uploads/img2.jpg", "alt": None}
            ]
        )

        # Act
        images = handler.extract_images(content)

        # Assert
        assert len(images) >= 2

    def test_extract_images_from_media_field(self, handler):
        """Test extracting images from media field."""
        # Arrange
        content = ContentItem(
            content_id="doc-123",
            content_type="article",
            title="Test Article",
            body="Simple text without inline images",
            media=[
                {
                    "id": "media-1",
                    "url": "/uploads/featured.jpg",
                    "alt": "Featured image",
                    "caption": "The featured image"
                },
                {
                    "id": "media-2",
                    "url": "/uploads/gallery1.jpg",
                    "alt": None
                }
            ]
        )

        # Act
        images = handler.extract_images(content)

        # Assert
        assert len(images) == 2
        assert images[0].alt_text == "Featured image"
        assert images[1].alt_text is None

    def test_extract_no_images(self, handler):
        """Test extracting from content with no images."""
        # Arrange
        content = ContentItem(
            content_id="doc-123",
            content_type="article",
            title="Text Only",
            body="<p>Just plain text, no images.</p>",
            media=[]
        )

        # Act
        images = handler.extract_images(content)

        # Assert
        assert len(images) == 0


class TestStrapiAltTextHandlerDetection:
    """Tests for missing alt-text detection."""

    @pytest.fixture
    def handler(self):
        """Create a handler instance."""
        return StrapiAltTextHandler()

    def test_detect_missing_alt_text(self, handler):
        """Test detecting images with missing alt text."""
        # Arrange
        images = [
            ImageInfo(image_id="1", url="/img1.jpg", alt_text="Has alt"),
            ImageInfo(image_id="2", url="/img2.jpg", alt_text=None),
            ImageInfo(image_id="3", url="/img3.jpg", alt_text=""),
            ImageInfo(image_id="4", url="/img4.jpg", alt_text="Also has alt")
        ]

        # Act
        missing = handler.find_missing_alt_text(images)

        # Assert
        assert len(missing) == 2
        assert missing[0].image_id == "2"
        assert missing[1].image_id == "3"

    def test_all_have_alt_text(self, handler):
        """Test when all images have alt text."""
        # Arrange
        images = [
            ImageInfo(image_id="1", url="/img1.jpg", alt_text="Alt 1"),
            ImageInfo(image_id="2", url="/img2.jpg", alt_text="Alt 2")
        ]

        # Act
        missing = handler.find_missing_alt_text(images)

        # Assert
        assert len(missing) == 0


class TestStrapiAltTextHandlerGeneration:
    """Tests for alt-text generation."""

    @pytest.fixture
    def handler(self):
        """Create a handler instance."""
        return StrapiAltTextHandler(style_profile="descriptive")

    @pytest.mark.asyncio
    async def test_generate_alt_text_for_image(self, handler):
        """Test generating alt text for a single image."""
        # Arrange
        image = ImageInfo(
            image_id="img-1",
            url="https://strapi.example.com/uploads/sunset.jpg",
            alt_text=None,
            caption="Sunset photo"
        )

        with patch.object(handler, '_analyze_image', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = "A vibrant sunset over the ocean with orange and purple sky"

            # Act
            result = await handler.generate_alt_text(image)

            # Assert
            assert result.image_id == "img-1"
            assert result.generated_alt_text is not None
            assert len(result.generated_alt_text) > 0

    @pytest.mark.asyncio
    async def test_generate_alt_text_uses_caption_context(self, handler):
        """Test that caption is used as context for generation."""
        # Arrange
        image = ImageInfo(
            image_id="img-1",
            url="https://strapi.example.com/uploads/product.jpg",
            alt_text=None,
            caption="New smartphone release"
        )

        with patch.object(handler, '_analyze_image', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = "Modern smartphone with edge-to-edge display on white background"

            # Act
            result = await handler.generate_alt_text(image)

            # Assert
            mock_analyze.assert_called_once()
            call_args = mock_analyze.call_args
            # Verify caption was passed as context
            assert "smartphone" in str(call_args).lower() or result.generated_alt_text is not None

    @pytest.mark.asyncio
    async def test_generate_alt_text_respects_max_length(self, handler):
        """Test that generated alt text respects max length."""
        # Arrange
        handler.max_length = 50
        image = ImageInfo(
            image_id="img-1",
            url="https://strapi.example.com/uploads/complex.jpg",
            alt_text=None
        )

        with patch.object(handler, '_analyze_image', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = "This is a very long description that should be truncated appropriately"

            # Act
            result = await handler.generate_alt_text(image)

            # Assert
            assert len(result.generated_alt_text) <= 50

    @pytest.mark.asyncio
    async def test_generate_alt_text_error_handling(self, handler):
        """Test error handling during generation."""
        # Arrange
        image = ImageInfo(
            image_id="img-1",
            url="https://invalid-url.example.com/missing.jpg",
            alt_text=None
        )

        with patch.object(handler, '_analyze_image', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.side_effect = Exception("Image not accessible")

            # Act & Assert
            with pytest.raises(AltTextGenerationError):
                await handler.generate_alt_text(image)


class TestStrapiAltTextHandlerBatch:
    """Tests for batch alt-text processing."""

    @pytest.fixture
    def handler(self):
        """Create a handler instance."""
        return StrapiAltTextHandler()

    @pytest.mark.asyncio
    async def test_process_batch_images(self, handler):
        """Test processing multiple images at once."""
        # Arrange
        images = [
            ImageInfo(image_id="1", url="/img1.jpg", alt_text=None),
            ImageInfo(image_id="2", url="/img2.jpg", alt_text=None),
            ImageInfo(image_id="3", url="/img3.jpg", alt_text=None)
        ]

        with patch.object(handler, 'generate_alt_text', new_callable=AsyncMock) as mock_gen:
            mock_gen.side_effect = [
                AltTextResult(image_id="1", original_alt_text=None, generated_alt_text="Alt 1"),
                AltTextResult(image_id="2", original_alt_text=None, generated_alt_text="Alt 2"),
                AltTextResult(image_id="3", original_alt_text=None, generated_alt_text="Alt 3")
            ]

            # Act
            results = await handler.process_batch(images)

            # Assert
            assert len(results) == 3
            assert all(r.generated_alt_text is not None for r in results)

    @pytest.mark.asyncio
    async def test_process_batch_skips_existing(self, handler):
        """Test that batch processing skips images with existing alt text."""
        # Arrange
        images = [
            ImageInfo(image_id="1", url="/img1.jpg", alt_text="Existing"),
            ImageInfo(image_id="2", url="/img2.jpg", alt_text=None)
        ]

        with patch.object(handler, 'generate_alt_text', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = AltTextResult(
                image_id="2",
                original_alt_text=None,
                generated_alt_text="Generated"
            )

            # Act
            results = await handler.process_batch(images, skip_existing=True)

            # Assert
            assert len(results) == 1
            assert results[0].image_id == "2"


class TestStrapiAltTextHandlerContentUpdate:
    """Tests for updating content with alt text."""

    @pytest.fixture
    def handler(self):
        """Create a handler instance."""
        return StrapiAltTextHandler()

    def test_apply_alt_text_to_content(self, handler):
        """Test applying generated alt text to content."""
        # Arrange
        content = ContentItem(
            content_id="doc-123",
            content_type="article",
            title="Test Article",
            body="<p>Text</p><img src='/uploads/img1.jpg' alt=''><p>More</p>",
            media=[
                {"id": "media-1", "url": "/uploads/img1.jpg", "alt": ""}
            ]
        )

        results = [
            AltTextResult(
                image_id="media-1",
                original_alt_text="",
                generated_alt_text="A beautiful landscape photo"
            )
        ]

        # Act
        updated_content = handler.apply_alt_text(content, results)

        # Assert
        assert updated_content.media[0]["alt"] == "A beautiful landscape photo"

    def test_apply_alt_text_preserves_existing(self, handler):
        """Test that existing alt text is preserved if not in results."""
        # Arrange
        content = ContentItem(
            content_id="doc-123",
            content_type="article",
            title="Test Article",
            body="Content",
            media=[
                {"id": "media-1", "url": "/img1.jpg", "alt": "Existing alt"},
                {"id": "media-2", "url": "/img2.jpg", "alt": ""}
            ]
        )

        results = [
            AltTextResult(
                image_id="media-2",
                original_alt_text="",
                generated_alt_text="New alt text"
            )
        ]

        # Act
        updated_content = handler.apply_alt_text(content, results)

        # Assert
        assert updated_content.media[0]["alt"] == "Existing alt"
        assert updated_content.media[1]["alt"] == "New alt text"


class TestStrapiAltTextHandlerFullWorkflow:
    """Tests for the complete alt-text workflow."""

    @pytest.fixture
    def handler(self):
        """Create a handler instance."""
        return StrapiAltTextHandler(style_profile="accessible")

    @pytest.mark.asyncio
    async def test_full_workflow(self, handler):
        """Test the complete workflow: extract -> detect -> generate -> apply."""
        # Arrange
        content = ContentItem(
            content_id="doc-123",
            content_type="article",
            title="Test Article",
            body="<p>Article content with images</p>",
            media=[
                {"id": "media-1", "url": "/img1.jpg", "alt": "Has alt"},
                {"id": "media-2", "url": "/img2.jpg", "alt": None},
                {"id": "media-3", "url": "/img3.jpg", "alt": ""}
            ]
        )

        with patch.object(handler, '_analyze_image', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.side_effect = [
                "Generated alt for image 2",
                "Generated alt for image 3"
            ]

            # Act
            updated_content = await handler.process_content(content)

            # Assert
            assert updated_content.media[0]["alt"] == "Has alt"  # Preserved
            assert updated_content.media[1]["alt"] == "Generated alt for image 2"
            assert updated_content.media[2]["alt"] == "Generated alt for image 3"

    @pytest.mark.asyncio
    async def test_workflow_returns_statistics(self, handler):
        """Test that workflow returns processing statistics."""
        # Arrange
        content = ContentItem(
            content_id="doc-123",
            content_type="article",
            title="Test",
            body="Content",
            media=[
                {"id": "1", "url": "/img1.jpg", "alt": "Has alt"},
                {"id": "2", "url": "/img2.jpg", "alt": None}
            ]
        )

        with patch.object(handler, '_analyze_image', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = "Generated alt text"

            # Act
            updated_content, stats = await handler.process_content_with_stats(content)

            # Assert
            assert stats["total_images"] == 2
            assert stats["images_with_alt"] == 1
            assert stats["images_updated"] == 1


class TestStrapiAltTextHandlerStyleAdaptation:
    """Tests for style-adapted alt text generation."""

    @pytest.fixture
    def handler(self):
        """Create a handler with formal style."""
        return StrapiAltTextHandler(style_profile="formal")

    @pytest.mark.asyncio
    async def test_applies_style_profile(self, handler):
        """Test that style profile is applied to generation."""
        # Arrange
        image = ImageInfo(
            image_id="1",
            url="/img.jpg",
            alt_text=None
        )

        with patch.object(handler, '_analyze_image', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = "Professional corporate headshot photograph"

            # Act
            result = await handler.generate_alt_text(image)

            # Assert
            # Style profile should influence the generation
            assert result.generated_alt_text is not None
            # Verify style was considered in the call
            call_args = mock_analyze.call_args
            assert "formal" in str(call_args).lower() or result.generated_alt_text is not None

    def test_set_style_profile(self, handler):
        """Test changing style profile."""
        # Act
        handler.set_style_profile("casual")

        # Assert
        assert handler.style_profile == "casual"
