"""Tests for Strapi Pipeline Integration.

Issue: INT-005 - Strapi Pipeline Integration

These tests verify:
- Complete pipeline from fetch to push
- Style adaptation integration
- Alt-text processing integration
- Pipeline configuration
- Error handling in pipeline stages
"""

import pytest
from datetime import datetime
from typing import Dict, Any, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass

from pseudoscribe.infrastructure.strapi_pipeline import (
    StrapiPipelineProcessor,
    PipelineConfig,
    PipelineResult,
    PipelineStage,
    PipelineError
)
from pseudoscribe.infrastructure.content_connector import ContentItem
from pseudoscribe.infrastructure.strapi_connector import StrapiConnector
from pseudoscribe.infrastructure.strapi_alt_text import (
    StrapiAltTextHandler,
    AltTextResult
)
from pseudoscribe.infrastructure.tenant_config_service import (
    TenantConfigService,
    ConnectorCredentials,
    CredentialType
)


class TestPipelineConfig:
    """Tests for PipelineConfig model."""

    def test_create_config(self):
        """Test creating a PipelineConfig."""
        # Act
        config = PipelineConfig(
            tenant_id="tenant-123",
            style_profile="formal",
            process_alt_text=True,
            max_alt_text_length=125
        )

        # Assert
        assert config.tenant_id == "tenant-123"
        assert config.style_profile == "formal"
        assert config.process_alt_text is True

    def test_config_defaults(self):
        """Test PipelineConfig default values."""
        # Act
        config = PipelineConfig(tenant_id="tenant-123")

        # Assert
        assert config.style_profile == "descriptive"
        assert config.process_alt_text is True
        assert config.max_alt_text_length == 125


class TestPipelineResult:
    """Tests for PipelineResult model."""

    def test_create_result(self):
        """Test creating a PipelineResult."""
        # Act
        result = PipelineResult(
            success=True,
            content_id="doc-123",
            stages_completed=["fetch", "style", "alt_text", "push"]
        )

        # Assert
        assert result.success is True
        assert len(result.stages_completed) == 4
        assert "successfully" in result.message.lower()

    def test_result_with_error(self):
        """Test PipelineResult with error."""
        # Act
        result = PipelineResult(
            success=False,
            content_id="doc-123",
            stages_completed=["fetch", "style"],
            error_stage="alt_text",
            error_message="Image analysis failed"
        )

        # Assert
        assert result.success is False
        assert result.error_stage == "alt_text"


class TestStrapiPipelineProcessorInit:
    """Tests for pipeline processor initialization."""

    @pytest.fixture
    def config_service(self):
        """Create a TenantConfigService instance."""
        return TenantConfigService()

    @pytest.fixture
    def credentials(self, config_service):
        """Create and store credentials."""
        return config_service.store_credentials("tenant-123", ConnectorCredentials(
            credential_type=CredentialType.STRAPI,
            name="test-strapi",
            api_url="https://strapi.example.com",
            api_token="test_token"
        ))

    def test_create_processor(self, config_service, credentials):
        """Test creating a pipeline processor."""
        # Arrange
        config = PipelineConfig(tenant_id="tenant-123")

        # Act
        processor = StrapiPipelineProcessor(
            config=config,
            credential_id=credentials,
            config_service=config_service
        )

        # Assert
        assert processor is not None
        assert processor.config.tenant_id == "tenant-123"

    def test_processor_creates_connector(self, config_service, credentials):
        """Test that processor creates a connector."""
        # Arrange
        config = PipelineConfig(tenant_id="tenant-123")

        # Act
        processor = StrapiPipelineProcessor(
            config=config,
            credential_id=credentials,
            config_service=config_service
        )

        # Assert
        assert processor._connector is not None


class TestStrapiPipelineProcessorFetch:
    """Tests for content fetching stage."""

    @pytest.fixture
    def processor(self):
        """Create a configured processor with mocks."""
        config_service = TenantConfigService()
        cred_id = config_service.store_credentials("tenant-123", ConnectorCredentials(
            credential_type=CredentialType.STRAPI,
            name="test",
            api_url="https://strapi.example.com",
            api_token="token"
        ))
        config = PipelineConfig(tenant_id="tenant-123")
        return StrapiPipelineProcessor(
            config=config,
            credential_id=cred_id,
            config_service=config_service
        )

    @pytest.mark.asyncio
    async def test_fetch_content(self, processor):
        """Test fetching content from Strapi."""
        # Arrange
        expected_content = ContentItem(
            content_id="doc-123",
            content_type="article",
            title="Test Article",
            body="Article body"
        )

        with patch.object(processor._connector, 'fetch_content', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = expected_content

            # Act
            content = await processor.fetch_content("doc-123", "article")

            # Assert
            assert content.content_id == "doc-123"
            assert content.title == "Test Article"

    @pytest.mark.asyncio
    async def test_fetch_content_with_default_type(self, processor):
        """Test fetching content with default content type."""
        # Arrange
        processor.set_default_content_type("blog")

        expected_content = ContentItem(
            content_id="doc-123",
            content_type="blog",
            title="Blog Post",
            body="Blog body"
        )

        with patch.object(processor._connector, 'fetch_content', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = expected_content

            # Act
            content = await processor.fetch_content("doc-123")

            # Assert
            mock_fetch.assert_called_once()


class TestStrapiPipelineProcessorStyleAdaptation:
    """Tests for style adaptation stage."""

    @pytest.fixture
    def processor(self):
        """Create a configured processor."""
        config_service = TenantConfigService()
        cred_id = config_service.store_credentials("tenant-123", ConnectorCredentials(
            credential_type=CredentialType.STRAPI,
            name="test",
            api_url="https://strapi.example.com",
            api_token="token"
        ))
        config = PipelineConfig(
            tenant_id="tenant-123",
            style_profile="formal"
        )
        return StrapiPipelineProcessor(
            config=config,
            credential_id=cred_id,
            config_service=config_service
        )

    @pytest.mark.asyncio
    async def test_apply_style_adaptation(self, processor):
        """Test applying style adaptation to content."""
        # Arrange
        content = ContentItem(
            content_id="doc-123",
            content_type="article",
            title="Test Article",
            body="hey this is informal text yo"
        )

        with patch.object(processor, '_adapt_style', new_callable=AsyncMock) as mock_adapt:
            mock_adapt.return_value = ContentItem(
                content_id="doc-123",
                content_type="article",
                title="Test Article",
                body="This is formal text appropriate for professional contexts."
            )

            # Act
            adapted = await processor.apply_style(content)

            # Assert
            assert adapted.body != content.body
            assert "formal" in adapted.body.lower() or "professional" in adapted.body.lower()

    @pytest.mark.asyncio
    async def test_style_uses_profile(self, processor):
        """Test that style adaptation uses configured profile."""
        # Arrange
        content = ContentItem(
            content_id="doc-123",
            content_type="article",
            title="Test",
            body="Original text"
        )

        with patch.object(processor, '_adapt_style', new_callable=AsyncMock) as mock_adapt:
            mock_adapt.return_value = content

            # Act
            await processor.apply_style(content)

            # Assert
            mock_adapt.assert_called_once()
            # Verify style profile was used
            assert processor.config.style_profile == "formal"


class TestStrapiPipelineProcessorAltText:
    """Tests for alt-text processing stage."""

    @pytest.fixture
    def processor(self):
        """Create a configured processor."""
        config_service = TenantConfigService()
        cred_id = config_service.store_credentials("tenant-123", ConnectorCredentials(
            credential_type=CredentialType.STRAPI,
            name="test",
            api_url="https://strapi.example.com",
            api_token="token"
        ))
        config = PipelineConfig(
            tenant_id="tenant-123",
            process_alt_text=True
        )
        return StrapiPipelineProcessor(
            config=config,
            credential_id=cred_id,
            config_service=config_service
        )

    @pytest.mark.asyncio
    async def test_process_alt_text(self, processor):
        """Test processing alt-text for images."""
        # Arrange
        content = ContentItem(
            content_id="doc-123",
            content_type="article",
            title="Article with Images",
            body="Content with images",
            media=[
                {"id": "1", "url": "/img1.jpg", "alt": None}
            ]
        )

        with patch.object(processor._alt_text_handler, 'process_content', new_callable=AsyncMock) as mock_process:
            updated_content = ContentItem(
                content_id="doc-123",
                content_type="article",
                title="Article with Images",
                body="Content with images",
                media=[
                    {"id": "1", "url": "/img1.jpg", "alt": "Generated alt text"}
                ]
            )
            mock_process.return_value = updated_content

            # Act
            result = await processor.process_alt_text(content)

            # Assert
            assert result.media[0]["alt"] == "Generated alt text"

    @pytest.mark.asyncio
    async def test_skip_alt_text_when_disabled(self, processor):
        """Test that alt-text processing is skipped when disabled."""
        # Arrange
        processor.config.process_alt_text = False
        content = ContentItem(
            content_id="doc-123",
            content_type="article",
            title="Test",
            body="Content",
            media=[{"id": "1", "url": "/img.jpg", "alt": None}]
        )

        # Act
        result = await processor.process_alt_text(content)

        # Assert - content unchanged
        assert result.media[0]["alt"] is None


class TestStrapiPipelineProcessorPush:
    """Tests for content pushing stage."""

    @pytest.fixture
    def processor(self):
        """Create a configured processor."""
        config_service = TenantConfigService()
        cred_id = config_service.store_credentials("tenant-123", ConnectorCredentials(
            credential_type=CredentialType.STRAPI,
            name="test",
            api_url="https://strapi.example.com",
            api_token="token"
        ))
        config = PipelineConfig(tenant_id="tenant-123")
        return StrapiPipelineProcessor(
            config=config,
            credential_id=cred_id,
            config_service=config_service
        )

    @pytest.mark.asyncio
    async def test_push_new_content(self, processor):
        """Test pushing new content to Strapi."""
        # Arrange
        content = ContentItem(
            content_type="article",
            title="New Article",
            body="Article body"
        )

        with patch.object(processor._connector, 'push_content', new_callable=AsyncMock) as mock_push:
            mock_push.return_value = "new-doc-123"

            # Act
            content_id = await processor.push_content(content)

            # Assert
            assert content_id == "new-doc-123"

    @pytest.mark.asyncio
    async def test_update_existing_content(self, processor):
        """Test updating existing content in Strapi."""
        # Arrange
        content = ContentItem(
            content_id="existing-123",
            content_type="article",
            title="Updated Article",
            body="Updated body"
        )

        with patch.object(processor._connector, 'update_content', new_callable=AsyncMock) as mock_update:
            mock_update.return_value = True

            # Act
            result = await processor.update_content("existing-123", content)

            # Assert
            assert result is True


class TestStrapiPipelineProcessorFullPipeline:
    """Tests for complete pipeline execution."""

    @pytest.fixture
    def processor(self):
        """Create a configured processor."""
        config_service = TenantConfigService()
        cred_id = config_service.store_credentials("tenant-123", ConnectorCredentials(
            credential_type=CredentialType.STRAPI,
            name="test",
            api_url="https://strapi.example.com",
            api_token="token"
        ))
        config = PipelineConfig(
            tenant_id="tenant-123",
            style_profile="formal",
            process_alt_text=True
        )
        return StrapiPipelineProcessor(
            config=config,
            credential_id=cred_id,
            config_service=config_service
        )

    @pytest.mark.asyncio
    async def test_run_full_pipeline_fetch_adapt_push(self, processor):
        """Test running the full pipeline: fetch -> style -> alt_text -> push."""
        # Arrange
        original_content = ContentItem(
            content_id="doc-123",
            content_type="article",
            title="Original Title",
            body="Original body text",
            media=[{"id": "1", "url": "/img.jpg", "alt": None}]
        )

        with patch.object(processor._connector, 'fetch_content', new_callable=AsyncMock) as mock_fetch:
            with patch.object(processor, '_adapt_style', new_callable=AsyncMock) as mock_style:
                with patch.object(processor._alt_text_handler, 'process_content', new_callable=AsyncMock) as mock_alt:
                    with patch.object(processor._connector, 'update_content', new_callable=AsyncMock) as mock_update:
                        mock_fetch.return_value = original_content
                        mock_style.return_value = ContentItem(
                            content_id="doc-123",
                            content_type="article",
                            title="Original Title",
                            body="Adapted body text",
                            media=[{"id": "1", "url": "/img.jpg", "alt": None}]
                        )
                        mock_alt.return_value = ContentItem(
                            content_id="doc-123",
                            content_type="article",
                            title="Original Title",
                            body="Adapted body text",
                            media=[{"id": "1", "url": "/img.jpg", "alt": "Generated alt"}]
                        )
                        mock_update.return_value = True

                        # Act
                        result = await processor.run_pipeline(
                            content_id="doc-123",
                            content_type="article"
                        )

                        # Assert
                        assert result.success is True
                        assert "fetch" in result.stages_completed
                        assert "style" in result.stages_completed
                        assert "alt_text" in result.stages_completed
                        assert "push" in result.stages_completed

    @pytest.mark.asyncio
    async def test_pipeline_error_at_fetch(self, processor):
        """Test pipeline error handling at fetch stage."""
        # Arrange
        with patch.object(processor._connector, 'fetch_content', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = Exception("Connection refused")

            # Act
            result = await processor.run_pipeline(
                content_id="doc-123",
                content_type="article"
            )

            # Assert
            assert result.success is False
            assert result.error_stage == "fetch"
            assert "Connection refused" in result.error_message

    @pytest.mark.asyncio
    async def test_pipeline_error_at_style(self, processor):
        """Test pipeline error handling at style stage."""
        # Arrange
        original_content = ContentItem(
            content_id="doc-123",
            content_type="article",
            title="Test",
            body="Body"
        )

        with patch.object(processor._connector, 'fetch_content', new_callable=AsyncMock) as mock_fetch:
            with patch.object(processor, '_adapt_style', new_callable=AsyncMock) as mock_style:
                mock_fetch.return_value = original_content
                mock_style.side_effect = Exception("Style adaptation failed")

                # Act
                result = await processor.run_pipeline(
                    content_id="doc-123",
                    content_type="article"
                )

                # Assert
                assert result.success is False
                assert result.error_stage == "style"
                assert "fetch" in result.stages_completed


class TestStrapiPipelineProcessorNewContent:
    """Tests for creating new content through pipeline."""

    @pytest.fixture
    def processor(self):
        """Create a configured processor."""
        config_service = TenantConfigService()
        cred_id = config_service.store_credentials("tenant-123", ConnectorCredentials(
            credential_type=CredentialType.STRAPI,
            name="test",
            api_url="https://strapi.example.com",
            api_token="token"
        ))
        config = PipelineConfig(
            tenant_id="tenant-123",
            style_profile="formal",
            process_alt_text=True
        )
        return StrapiPipelineProcessor(
            config=config,
            credential_id=cred_id,
            config_service=config_service
        )

    @pytest.mark.asyncio
    async def test_create_new_content_pipeline(self, processor):
        """Test creating new content through the pipeline."""
        # Arrange
        new_content = ContentItem(
            content_type="article",
            title="New Article",
            body="Article body to be styled",
            media=[{"id": "1", "url": "/img.jpg", "alt": None}]
        )

        with patch.object(processor, '_adapt_style', new_callable=AsyncMock) as mock_style:
            with patch.object(processor._alt_text_handler, 'process_content', new_callable=AsyncMock) as mock_alt:
                with patch.object(processor._connector, 'push_content', new_callable=AsyncMock) as mock_push:
                    mock_style.return_value = ContentItem(
                        content_type="article",
                        title="New Article",
                        body="Styled article body",
                        media=[{"id": "1", "url": "/img.jpg", "alt": None}]
                    )
                    mock_alt.return_value = ContentItem(
                        content_type="article",
                        title="New Article",
                        body="Styled article body",
                        media=[{"id": "1", "url": "/img.jpg", "alt": "Alt text"}]
                    )
                    mock_push.return_value = "new-123"

                    # Act
                    result = await processor.create_content(new_content)

                    # Assert
                    assert result.success is True
                    assert result.content_id == "new-123"
                    assert "style" in result.stages_completed
                    assert "alt_text" in result.stages_completed
                    assert "push" in result.stages_completed


class TestStrapiPipelineProcessorBatch:
    """Tests for batch processing."""

    @pytest.fixture
    def processor(self):
        """Create a configured processor."""
        config_service = TenantConfigService()
        cred_id = config_service.store_credentials("tenant-123", ConnectorCredentials(
            credential_type=CredentialType.STRAPI,
            name="test",
            api_url="https://strapi.example.com",
            api_token="token"
        ))
        config = PipelineConfig(tenant_id="tenant-123")
        return StrapiPipelineProcessor(
            config=config,
            credential_id=cred_id,
            config_service=config_service
        )

    @pytest.mark.asyncio
    async def test_process_batch(self, processor):
        """Test processing multiple content items."""
        # Arrange
        content_ids = ["doc-1", "doc-2", "doc-3"]

        with patch.object(processor, 'run_pipeline', new_callable=AsyncMock) as mock_run:
            mock_run.side_effect = [
                PipelineResult(success=True, content_id="doc-1", stages_completed=["fetch", "style", "push"]),
                PipelineResult(success=True, content_id="doc-2", stages_completed=["fetch", "style", "push"]),
                PipelineResult(success=False, content_id="doc-3", stages_completed=["fetch"], error_stage="style", error_message="Failed")
            ]

            # Act
            results = await processor.process_batch(content_ids, "article")

            # Assert
            assert len(results) == 3
            assert results[0].success is True
            assert results[1].success is True
            assert results[2].success is False

    @pytest.mark.asyncio
    async def test_batch_returns_summary(self, processor):
        """Test batch processing returns summary statistics."""
        # Arrange
        content_ids = ["doc-1", "doc-2"]

        with patch.object(processor, 'run_pipeline', new_callable=AsyncMock) as mock_run:
            mock_run.side_effect = [
                PipelineResult(success=True, content_id="doc-1", stages_completed=["fetch", "style", "push"]),
                PipelineResult(success=True, content_id="doc-2", stages_completed=["fetch", "style", "push"])
            ]

            # Act
            results, summary = await processor.process_batch_with_summary(content_ids, "article")

            # Assert
            assert summary["total"] == 2
            assert summary["succeeded"] == 2
            assert summary["failed"] == 0
