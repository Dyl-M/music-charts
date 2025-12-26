"""Unit tests for pipeline base classes.

Tests PipelineStage abstract base class and Pipeline orchestrator.
"""
from abc import ABC
# Standard library
from pathlib import Path
from unittest.mock import MagicMock, patch

# Third-party
import pytest

# Local
from msc.pipeline.base import Pipeline, PipelineStage


class ConcretePipelineStage(PipelineStage[list[str], list[str]]):
    """Concrete implementation for testing."""

    @property
    def stage_name(self) -> str:
        """Return stage name."""
        return "TestStage"

    @staticmethod
    def extract() -> list[str]:
        """Extract test data."""
        return ["item1", "item2"]

    @staticmethod
    def transform(data: list[str]) -> list[str]:
        """Transform test data."""
        return [item.upper() for item in data]

    def load(self, data: list[str]) -> None:
        """Load test data."""
        raise NotImplementedError()


class FailingStage(PipelineStage[list[str], list[str]]):
    """Stage that fails during transform."""

    @property
    def stage_name(self) -> str:
        """Return stage name."""
        return "FailingStage"

    @staticmethod
    def extract() -> list[str]:
        """Extract test data."""
        return ["item"]

    @staticmethod
    def transform(data: list[str]) -> list[str]:
        """Raise an error."""
        raise ValueError("Transform failed")

    def load(self, data: list[str]) -> None:
        """Load test data."""
        raise NotImplementedError()


class TestPipelineStageInterface:
    """Tests for PipelineStage abstract interface."""

    @staticmethod
    def test_cannot_instantiate_directly() -> None:
        """Should not allow direct instantiation."""
        with pytest.raises(TypeError, match="abstract"):
            # noinspection PyAbstractClass
            PipelineStage()

    @staticmethod
    def test_requires_stage_name() -> None:
        """Should require stage_name property."""

        class IncompleteStage(PipelineStage, ABC):
            """Stage missing stage_name."""

            def extract(self):
                return []

            def transform(self, data):
                return data

            def load(self, data):
                raise NotImplementedError()

        with pytest.raises(TypeError, match="stage_name"):
            # noinspection PyAbstractClass
            IncompleteStage()

    @staticmethod
    def test_requires_extract() -> None:
        """Should require extract method."""

        class IncompleteStage(PipelineStage, ABC):
            """Stage missing extract."""

            @property
            def stage_name(self) -> str:
                return "Test"

            def transform(self, data):
                return data

            def load(self, data):
                raise NotImplementedError()

        with pytest.raises(TypeError, match="extract"):
            # noinspection PyAbstractClass
            IncompleteStage()

    @staticmethod
    def test_requires_transform() -> None:
        """Should require transform method."""

        class IncompleteStage(PipelineStage, ABC):
            """Stage missing transform."""

            @property
            def stage_name(self) -> str:
                return "Test"

            def extract(self):
                return []

            def load(self, data):
                raise NotImplementedError()

        with pytest.raises(TypeError, match="transform"):
            # noinspection PyAbstractClass
            IncompleteStage()

    @staticmethod
    def test_requires_load() -> None:
        """Should require load method."""

        class IncompleteStage(PipelineStage, ABC):
            """Stage missing load."""

            @property
            def stage_name(self) -> str:
                return "Test"

            def extract(self):
                return []

            def transform(self, data):
                return data

        with pytest.raises(TypeError, match="load"):
            # noinspection PyAbstractClass
            IncompleteStage()


class TestPipelineStageInit:
    """Tests for PipelineStage initialization."""

    @staticmethod
    def test_uses_global_settings() -> None:
        """Should use global settings when none provided."""
        with patch("msc.pipeline.base.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_get_settings.return_value = mock_settings

            stage = ConcretePipelineStage()

            assert stage.settings is mock_settings

    @staticmethod
    def test_accepts_custom_settings() -> None:
        """Should accept custom settings."""
        mock_settings = MagicMock()

        stage = ConcretePipelineStage(settings=mock_settings)

        assert stage.settings is mock_settings

    @staticmethod
    def test_accepts_input_path() -> None:
        """Should accept input path override."""
        input_path = Path("/custom/input")

        stage = ConcretePipelineStage(input_path=input_path)

        assert stage.input_path == input_path

    @staticmethod
    def test_accepts_output_path() -> None:
        """Should accept output path override."""
        output_path = Path("/custom/output")

        stage = ConcretePipelineStage(output_path=output_path)

        assert stage.output_path == output_path

    @staticmethod
    def test_creates_logger() -> None:
        """Should create logger with class name."""
        stage = ConcretePipelineStage()

        assert stage.logger is not None


class TestPipelineStageRun:
    """Tests for PipelineStage.run method."""

    @staticmethod
    def test_run_calls_extract_transform_load() -> None:
        """Should call extract, transform, load in sequence."""
        stage = ConcretePipelineStage()

        result = stage.run()

        assert result == ["ITEM1", "ITEM2"]

    @staticmethod
    def test_run_returns_transformed_data() -> None:
        """Should return transformed data."""
        stage = ConcretePipelineStage()

        result = stage.run()

        assert isinstance(result, list)
        assert len(result) == 2


class TestPipelineInit:
    """Tests for Pipeline initialization."""

    @staticmethod
    def test_uses_global_settings() -> None:
        """Should use global settings when none provided."""
        with patch("msc.pipeline.base.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_get_settings.return_value = mock_settings

            pipeline = Pipeline()

            assert pipeline.settings is mock_settings

    @staticmethod
    def test_accepts_custom_settings() -> None:
        """Should accept custom settings."""
        mock_settings = MagicMock()

        pipeline = Pipeline(settings=mock_settings)

        assert pipeline.settings is mock_settings

    @staticmethod
    def test_starts_with_empty_stages() -> None:
        """Should start with no stages."""
        pipeline = Pipeline()

        assert pipeline._stages == []


class TestPipelineAddStage:
    """Tests for Pipeline.add_stage method."""

    @staticmethod
    def test_adds_stage_to_list() -> None:
        """Should add stage to internal list."""
        pipeline = Pipeline()
        stage = ConcretePipelineStage()

        pipeline.add_stage(stage)

        assert len(pipeline._stages) == 1
        assert pipeline._stages[0] is stage

    @staticmethod
    def test_returns_self_for_chaining() -> None:
        """Should return self for method chaining."""
        pipeline = Pipeline()
        stage = ConcretePipelineStage()

        result = pipeline.add_stage(stage)

        assert result is pipeline

    @staticmethod
    def test_can_add_multiple_stages() -> None:
        """Should add multiple stages."""
        pipeline = Pipeline()
        stage1 = ConcretePipelineStage()
        stage2 = ConcretePipelineStage()

        pipeline.add_stage(stage1).add_stage(stage2)

        assert len(pipeline._stages) == 2


class TestPipelineRun:
    """Tests for Pipeline.run method."""

    @staticmethod
    def test_runs_all_stages() -> None:
        """Should run all stages when no filter provided."""
        pipeline = Pipeline()
        stage = ConcretePipelineStage()
        pipeline.add_stage(stage)

        results = pipeline.run()

        assert "TestStage" in results
        assert results["TestStage"] == ["ITEM1", "ITEM2"]

    @staticmethod
    def test_filters_stages_by_name() -> None:
        """Should only run specified stages."""
        pipeline = Pipeline()
        stage1 = ConcretePipelineStage()
        stage2 = ConcretePipelineStage()
        pipeline.add_stage(stage1).add_stage(stage2)

        results = pipeline.run(stages=["TestStage"])

        # Both stages have same name, results dict has 1 key (last result wins)
        assert len(results) == 1
        assert "TestStage" in results

    @staticmethod
    def test_skips_stages_not_in_filter() -> None:
        """Should skip stages not in filter list."""
        pipeline = Pipeline()
        stage = ConcretePipelineStage()
        pipeline.add_stage(stage)

        results = pipeline.run(stages=["NonexistentStage"])

        assert len(results) == 0

    @staticmethod
    def test_raises_on_stage_failure() -> None:
        """Should raise exception when stage fails."""
        pipeline = Pipeline()
        stage = FailingStage()
        pipeline.add_stage(stage)

        with pytest.raises(ValueError, match="Transform failed"):
            pipeline.run()

    @staticmethod
    def test_returns_results_dict() -> None:
        """Should return dict mapping stage names to results."""
        pipeline = Pipeline()
        stage = ConcretePipelineStage()
        pipeline.add_stage(stage)

        results = pipeline.run()

        assert isinstance(results, dict)
        assert "TestStage" in results
