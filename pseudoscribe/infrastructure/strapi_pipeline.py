"""Strapi Pipeline Integration.

Issue: INT-005 - Strapi Pipeline Integration

This module provides the complete pipeline for Strapi content processing:
- Content fetching from Strapi
- Style adaptation
- Alt-text processing for images
- Content pushing back to Strapi
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum

from pseudoscribe.infrastructure.content_connector import ContentItem
from pseudoscribe.infrastructure.strapi_connector import StrapiConnector
from pseudoscribe.infrastructure.strapi_alt_text import StrapiAltTextHandler
from pseudoscribe.infrastructure.tenant_config_service import TenantConfigService


class PipelineStage(Enum):
    """Pipeline stage identifiers."""
    FETCH = "fetch"
    STYLE = "style"
    ALT_TEXT = "alt_text"
    PUSH = "push"


class PipelineError(Exception):
    """Raised when a pipeline stage fails."""

    def __init__(self, stage: str, message: str):
        self.stage = stage
        self.message = message
        super().__init__(f"Pipeline error at {stage}: {message}")


@dataclass
class PipelineConfig:
    """Configuration for the Strapi pipeline."""
    tenant_id: str
    style_profile: str = "descriptive"
    process_alt_text: bool = True
    max_alt_text_length: int = 125
    default_content_type: str = "article"


@dataclass
class PipelineResult:
    """Result of a pipeline execution."""
    success: bool
    content_id: Optional[str] = None
    stages_completed: List[str] = field(default_factory=list)
    error_stage: Optional[str] = None
    error_message: Optional[str] = None
    content: Optional[ContentItem] = None
    statistics: Dict[str, Any] = field(default_factory=dict)

    @property
    def message(self) -> str:
        """Get a human-readable message."""
        if self.success:
            return f"Pipeline completed successfully for {self.content_id}"
        return f"Pipeline failed at {self.error_stage}: {self.error_message}"


class StrapiPipelineProcessor:
    """Complete pipeline processor for Strapi content.

    Orchestrates the full workflow:
    1. Fetch content from Strapi
    2. Apply style adaptation
    3. Process alt-text for images
    4. Push/update content back to Strapi
    """

    def __init__(
        self,
        config: PipelineConfig,
        credential_id: str,
        config_service: TenantConfigService
    ):
        """Initialize the pipeline processor.

        Args:
            config: Pipeline configuration
            credential_id: ID of Strapi credentials
            config_service: Tenant config service
        """
        self.config = config
        self._credential_id = credential_id
        self._config_service = config_service

        # Initialize components
        self._connector = StrapiConnector(
            tenant_id=config.tenant_id,
            credential_id=credential_id,
            config_service=config_service
        )

        self._alt_text_handler = StrapiAltTextHandler(
            style_profile=config.style_profile,
            max_length=config.max_alt_text_length
        )

        self._default_content_type = config.default_content_type

    def set_default_content_type(self, content_type: str) -> None:
        """Set the default content type.

        Args:
            content_type: The default content type
        """
        self._default_content_type = content_type
        self._connector.set_default_content_type(content_type)

    async def fetch_content(
        self,
        content_id: str,
        content_type: Optional[str] = None
    ) -> ContentItem:
        """Fetch content from Strapi.

        Args:
            content_id: The content document ID
            content_type: Optional content type

        Returns:
            ContentItem from Strapi
        """
        return await self._connector.fetch_content(
            content_id,
            content_type=content_type or self._default_content_type
        )

    async def _adapt_style(self, content: ContentItem) -> ContentItem:
        """Apply style adaptation to content.

        This is a placeholder for the actual style adaptation.
        In production, this would call the style adapter service.

        Args:
            content: The content to adapt

        Returns:
            Style-adapted content
        """
        # Placeholder - in production, this would:
        # 1. Call the style profiler to analyze current style
        # 2. Call the style adapter to transform to target style
        # For now, return content unchanged
        return content

    async def apply_style(self, content: ContentItem) -> ContentItem:
        """Apply style adaptation to content.

        Args:
            content: The content to adapt

        Returns:
            Style-adapted content
        """
        return await self._adapt_style(content)

    async def process_alt_text(self, content: ContentItem) -> ContentItem:
        """Process alt-text for images in content.

        Args:
            content: The content to process

        Returns:
            Content with processed alt-text
        """
        if not self.config.process_alt_text:
            return content

        return await self._alt_text_handler.process_content(content)

    async def push_content(self, content: ContentItem) -> str:
        """Push new content to Strapi.

        Args:
            content: The content to push

        Returns:
            The created content ID
        """
        return await self._connector.push_content(content)

    async def update_content(
        self,
        content_id: str,
        content: ContentItem
    ) -> bool:
        """Update existing content in Strapi.

        Args:
            content_id: The content document ID
            content: The updated content

        Returns:
            True if successful
        """
        return await self._connector.update_content(content_id, content)

    async def run_pipeline(
        self,
        content_id: str,
        content_type: Optional[str] = None
    ) -> PipelineResult:
        """Run the complete pipeline for existing content.

        Stages: fetch -> style -> alt_text -> push

        Args:
            content_id: The content document ID to process
            content_type: Optional content type

        Returns:
            PipelineResult with execution details
        """
        stages_completed = []
        content = None

        try:
            # Stage 1: Fetch
            content = await self.fetch_content(
                content_id,
                content_type or self._default_content_type
            )
            stages_completed.append("fetch")

            # Stage 2: Style adaptation
            content = await self.apply_style(content)
            stages_completed.append("style")

            # Stage 3: Alt-text processing
            content = await self.process_alt_text(content)
            stages_completed.append("alt_text")

            # Stage 4: Push back to Strapi
            await self.update_content(content_id, content)
            stages_completed.append("push")

            return PipelineResult(
                success=True,
                content_id=content_id,
                stages_completed=stages_completed,
                content=content
            )

        except Exception as e:
            # Determine which stage failed
            stage_order = ["fetch", "style", "alt_text", "push"]
            error_stage = stage_order[len(stages_completed)] if len(stages_completed) < len(stage_order) else "unknown"

            return PipelineResult(
                success=False,
                content_id=content_id,
                stages_completed=stages_completed,
                error_stage=error_stage,
                error_message=str(e),
                content=content
            )

    async def create_content(self, content: ContentItem) -> PipelineResult:
        """Create new content through the pipeline.

        Stages: style -> alt_text -> push

        Args:
            content: The new content to create

        Returns:
            PipelineResult with execution details
        """
        stages_completed = []
        processed_content = content

        try:
            # Stage 1: Style adaptation
            processed_content = await self.apply_style(processed_content)
            stages_completed.append("style")

            # Stage 2: Alt-text processing
            processed_content = await self.process_alt_text(processed_content)
            stages_completed.append("alt_text")

            # Stage 3: Push to Strapi
            content_id = await self.push_content(processed_content)
            stages_completed.append("push")

            return PipelineResult(
                success=True,
                content_id=content_id,
                stages_completed=stages_completed,
                content=processed_content
            )

        except Exception as e:
            stage_order = ["style", "alt_text", "push"]
            error_stage = stage_order[len(stages_completed)] if len(stages_completed) < len(stage_order) else "unknown"

            return PipelineResult(
                success=False,
                content_id=None,
                stages_completed=stages_completed,
                error_stage=error_stage,
                error_message=str(e),
                content=processed_content
            )

    async def process_batch(
        self,
        content_ids: List[str],
        content_type: str
    ) -> List[PipelineResult]:
        """Process multiple content items.

        Args:
            content_ids: List of content IDs to process
            content_type: The content type

        Returns:
            List of PipelineResults
        """
        results = []
        for content_id in content_ids:
            result = await self.run_pipeline(content_id, content_type)
            results.append(result)
        return results

    async def process_batch_with_summary(
        self,
        content_ids: List[str],
        content_type: str
    ) -> Tuple[List[PipelineResult], Dict[str, int]]:
        """Process multiple content items with summary.

        Args:
            content_ids: List of content IDs to process
            content_type: The content type

        Returns:
            Tuple of (results list, summary dict)
        """
        results = await self.process_batch(content_ids, content_type)

        summary = {
            "total": len(results),
            "succeeded": sum(1 for r in results if r.success),
            "failed": sum(1 for r in results if not r.success)
        }

        return results, summary
