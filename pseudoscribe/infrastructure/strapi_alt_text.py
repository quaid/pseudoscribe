"""Strapi Alt-Text Handler.

Issue: INT-004 - Strapi Alt-Text Handler

This module provides alt-text handling for Strapi content:
- Image extraction from content
- Missing alt-text detection
- Alt-text generation with style adaptation
- Content updating with generated alt-text
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple

from pseudoscribe.infrastructure.content_connector import ContentItem


class AltTextGenerationError(Exception):
    """Raised when alt-text generation fails."""
    pass


@dataclass
class ImageInfo:
    """Information about an image in content."""
    image_id: str
    url: str
    alt_text: Optional[str] = None
    caption: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def has_alt_text(self) -> bool:
        """Check if image has non-empty alt text.

        Returns:
            True if alt text exists and is non-empty
        """
        return bool(self.alt_text and self.alt_text.strip())


@dataclass
class AltTextResult:
    """Result of alt-text generation."""
    image_id: str
    original_alt_text: Optional[str]
    generated_alt_text: Optional[str]
    confidence: float = 0.0
    error: Optional[str] = None

    def was_updated(self) -> bool:
        """Check if alt text was updated.

        Returns:
            True if new alt text was generated
        """
        return self.generated_alt_text is not None and len(self.generated_alt_text) > 0


class StrapiAltTextHandler:
    """Handler for alt-text processing in Strapi content.

    Provides functionality to:
    - Extract images from content
    - Detect missing alt-text
    - Generate accessible alt-text with style adaptation
    - Update content with generated alt-text
    """

    def __init__(
        self,
        style_profile: str = "descriptive",
        max_length: int = 125
    ):
        """Initialize the alt-text handler.

        Args:
            style_profile: Style profile for alt-text generation
            max_length: Maximum length for generated alt-text
        """
        self.style_profile = style_profile
        self.max_length = max_length

    def set_style_profile(self, style_profile: str) -> None:
        """Set the style profile for alt-text generation.

        Args:
            style_profile: The style profile to use
        """
        self.style_profile = style_profile

    def extract_images(self, content: ContentItem) -> List[ImageInfo]:
        """Extract images from content.

        Extracts images from both the media field and inline HTML.

        Args:
            content: The content to extract images from

        Returns:
            List of ImageInfo objects
        """
        images = []

        # Extract from media field
        for media_item in content.media:
            if isinstance(media_item, dict):
                image_id = media_item.get("id", str(len(images)))
                url = media_item.get("url", "")
                alt_text = media_item.get("alt")
                caption = media_item.get("caption")

                images.append(ImageInfo(
                    image_id=str(image_id),
                    url=url,
                    alt_text=alt_text,
                    caption=caption,
                    metadata=media_item
                ))

        # Extract inline images from HTML body
        if content.body:
            inline_images = self._extract_inline_images(content.body)
            # Add inline images that aren't already in media
            existing_urls = {img.url for img in images}
            for inline_img in inline_images:
                if inline_img.url not in existing_urls:
                    images.append(inline_img)

        return images

    def _extract_inline_images(self, html: str) -> List[ImageInfo]:
        """Extract images from HTML content.

        Args:
            html: HTML content string

        Returns:
            List of ImageInfo for inline images
        """
        images = []

        # Simple regex to find img tags
        img_pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*(?:alt=["\']([^"\']*)["\'])?[^>]*>'
        matches = re.findall(img_pattern, html, re.IGNORECASE)

        for i, match in enumerate(matches):
            src = match[0] if len(match) > 0 else ""
            alt = match[1] if len(match) > 1 else None

            images.append(ImageInfo(
                image_id=f"inline-{i}",
                url=src,
                alt_text=alt if alt else None
            ))

        return images

    def find_missing_alt_text(self, images: List[ImageInfo]) -> List[ImageInfo]:
        """Find images with missing or empty alt text.

        Args:
            images: List of images to check

        Returns:
            List of images without alt text
        """
        return [img for img in images if not img.has_alt_text()]

    async def _analyze_image(
        self,
        image: ImageInfo,
        style_profile: str
    ) -> str:
        """Analyze an image and generate description.

        This is a placeholder for the actual image analysis.
        In production, this would call an AI vision model.

        Args:
            image: The image to analyze
            style_profile: Style to apply to description

        Returns:
            Generated description
        """
        # Placeholder - in production, this would:
        # 1. Fetch the image from the URL
        # 2. Call an AI vision model
        # 3. Apply style adaptation to the result

        # For now, use caption as context if available
        context = image.caption or ""
        return f"Image: {context}" if context else "Descriptive image content"

    async def generate_alt_text(self, image: ImageInfo) -> AltTextResult:
        """Generate alt text for an image.

        Args:
            image: The image to generate alt text for

        Returns:
            AltTextResult with generated alt text

        Raises:
            AltTextGenerationError: If generation fails
        """
        try:
            description = await self._analyze_image(image, self.style_profile)

            # Truncate to max length if needed
            if len(description) > self.max_length:
                # Try to truncate at word boundary
                description = description[:self.max_length]
                last_space = description.rfind(' ')
                if last_space > self.max_length * 0.7:
                    description = description[:last_space]

            return AltTextResult(
                image_id=image.image_id,
                original_alt_text=image.alt_text,
                generated_alt_text=description,
                confidence=0.85
            )

        except Exception as e:
            raise AltTextGenerationError(
                f"Failed to generate alt text for image {image.image_id}: {str(e)}"
            ) from e

    async def process_batch(
        self,
        images: List[ImageInfo],
        skip_existing: bool = False
    ) -> List[AltTextResult]:
        """Process multiple images in batch.

        Args:
            images: List of images to process
            skip_existing: If True, skip images that already have alt text

        Returns:
            List of AltTextResult for processed images
        """
        results = []

        for image in images:
            if skip_existing and image.has_alt_text():
                continue

            try:
                result = await self.generate_alt_text(image)
                results.append(result)
            except AltTextGenerationError as e:
                results.append(AltTextResult(
                    image_id=image.image_id,
                    original_alt_text=image.alt_text,
                    generated_alt_text=None,
                    error=str(e)
                ))

        return results

    def apply_alt_text(
        self,
        content: ContentItem,
        results: List[AltTextResult]
    ) -> ContentItem:
        """Apply generated alt text to content.

        Args:
            content: The original content
            results: List of alt text generation results

        Returns:
            Updated content with new alt text
        """
        # Create a lookup for results
        result_lookup = {r.image_id: r for r in results if r.generated_alt_text}

        # Update media items
        updated_media = []
        for media_item in content.media:
            if isinstance(media_item, dict):
                media_id = str(media_item.get("id", ""))
                if media_id in result_lookup:
                    updated_item = dict(media_item)
                    updated_item["alt"] = result_lookup[media_id].generated_alt_text
                    updated_media.append(updated_item)
                else:
                    updated_media.append(media_item)
            else:
                updated_media.append(media_item)

        # Create updated content
        return ContentItem(
            content_id=content.content_id,
            content_type=content.content_type,
            title=content.title,
            body=content.body,
            metadata=content.metadata,
            created_at=content.created_at,
            updated_at=content.updated_at,
            status=content.status,
            locale=content.locale,
            media=updated_media
        )

    async def process_content(self, content: ContentItem) -> ContentItem:
        """Process content and add missing alt text.

        This is the main workflow method that:
        1. Extracts images from content
        2. Finds images missing alt text
        3. Generates alt text for those images
        4. Returns updated content

        Args:
            content: The content to process

        Returns:
            Updated content with generated alt text
        """
        # Extract all images
        images = self.extract_images(content)

        # Find images missing alt text
        missing = self.find_missing_alt_text(images)

        if not missing:
            return content

        # Generate alt text for missing images
        results = await self.process_batch(missing)

        # Apply results to content
        return self.apply_alt_text(content, results)

    async def process_content_with_stats(
        self,
        content: ContentItem
    ) -> Tuple[ContentItem, Dict[str, int]]:
        """Process content and return with statistics.

        Args:
            content: The content to process

        Returns:
            Tuple of (updated content, statistics dict)
        """
        # Extract all images
        images = self.extract_images(content)

        # Find images missing alt text
        missing = self.find_missing_alt_text(images)

        stats = {
            "total_images": len(images),
            "images_with_alt": len(images) - len(missing),
            "images_updated": 0
        }

        if not missing:
            return content, stats

        # Generate alt text for missing images
        results = await self.process_batch(missing)

        # Count successful updates
        stats["images_updated"] = sum(1 for r in results if r.was_updated())

        # Apply results to content
        updated_content = self.apply_alt_text(content, results)

        return updated_content, stats
