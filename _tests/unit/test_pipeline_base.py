"""Tests for pipeline base classes.

Tests PipelineStage abstract base class and Pipeline orchestrator.
"""

# Standard library
from pathlib import Path

# Third-party
import pytest

# Local
from msc.config.settings import Settings
from msc.pipeline.base import Pipeline, PipelineStage


# === Test Implementation ===


class ConcretePipelineStage(PipelineStage[list[str], list[str]]):
    """Concrete implementation for testing PipelineStage."""

    @property
    def stage_name(self) -> str:
        """Return stage name."""
        return "Test Stage"

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
    """Stage that raises an exception for testing."""

    @property
    def stage_name(self) -> str:
        """Return stage name."""
        return "Failing Stage"

    @staticmethod
    def extract() -> list[str]:
        """Extract test data."""
        return ["item1"]

    @staticmethod
    def transform(data: list[str]) -> list[str]:
        """Transform test data."""
        return data

    @staticmethod
    def load(data: list[str]) -> None:
        """Raise exception during load."""
        raise RuntimeError("Load failed")


# === PipelineStage Tests ===


class TestPipelineStage:
    """Tests for PipelineStage abstract base class."""

    @staticmethod
    def test_init_with_defaults() -> None:
        """Test initialization with default settings."""
        stage = ConcretePipelineStage()

        assert stage.settings is not None
        assert stage.input_path is None
        assert stage.output_path is None
        assert stage.logger is not None

    @staticmethod
    def test_init_with_custom_settings(tmp_path: Path) -> None:
        """Test initialization with custom settings and paths."""
        settings = Settings(year=2025)
        input_path = tmp_path / "input"
        output_path = tmp_path / "output"

        stage = ConcretePipelineStage(
            settings=settings,
            input_path=input_path,
            output_path=output_path,
        )

        assert stage.settings == settings
        assert stage.input_path == input_path
        assert stage.output_path == output_path

    @staticmethod
    def test_validate_input_returns_true() -> None:
        """Test validate_input default implementation returns True."""
        stage = ConcretePipelineStage()

        result = stage.validate_input(["test"])

        assert result is True

    @staticmethod
    def test_validate_output_returns_true() -> None:
        """Test validate_output default implementation returns True."""
        stage = ConcretePipelineStage()

        result = stage.validate_output(["TEST"])

        assert result is True

    @staticmethod
    def test_run_executes_etl_pipeline() -> None:
        """Test run method executes extract, transform, load."""
        stage = ConcretePipelineStage()

        result = stage.run()

        # Should return transformed data
        assert result == ["ITEM1", "ITEM2"]

    @staticmethod
    def test_abstract_methods_raise_not_implemented() -> None:
        """Test abstract methods raise NotImplementedError."""
        # Cannot instantiate abstract class directly - intentional test
        with pytest.raises(TypeError):
            # noinspection PyAbstractClass
            PipelineStage()  # type: ignore[abstract]


# === Pipeline Tests ===


class TestPipeline:
    """Tests for Pipeline orchestrator."""

    @staticmethod
    def test_init_with_defaults() -> None:
        """Test Pipeline initialization with defaults."""
        pipeline = Pipeline()

        assert pipeline.settings is not None
        assert pipeline.logger is not None
        assert pipeline._stages == []

    @staticmethod
    def test_init_with_custom_settings() -> None:
        """Test Pipeline initialization with custom settings."""
        settings = Settings(year=2025)

        pipeline = Pipeline(settings=settings)

        assert pipeline.settings == settings

    @staticmethod
    def test_add_stage() -> None:
        """Test adding a stage to the pipeline."""
        pipeline = Pipeline()
        stage = ConcretePipelineStage()

        result = pipeline.add_stage(stage)

        # Should return self for chaining
        assert result is pipeline
        assert len(pipeline._stages) == 1
        assert pipeline._stages[0] is stage

    @staticmethod
    def test_add_multiple_stages() -> None:
        """Test adding multiple stages."""
        pipeline = Pipeline()
        stage1 = ConcretePipelineStage()
        stage2 = ConcretePipelineStage()

        pipeline.add_stage(stage1).add_stage(stage2)

        assert len(pipeline._stages) == 2

    @staticmethod
    def test_run_all_stages() -> None:
        """Test running all stages."""

        class Stage1(ConcretePipelineStage):
            """First stage."""

            @property
            def stage_name(self) -> str:
                """Return stage name."""
                return "Stage 1"

        class Stage2(ConcretePipelineStage):
            """Second stage."""

            @property
            def stage_name(self) -> str:
                """Return stage name."""
                return "Stage 2"

        pipeline = Pipeline()

        pipeline.add_stage(Stage1()).add_stage(Stage2())

        results = pipeline.run()

        # Should return results from both stages
        assert len(results) == 2
        assert "Stage 1" in results
        assert "Stage 2" in results
        assert results["Stage 1"] == ["ITEM1", "ITEM2"]
        assert results["Stage 2"] == ["ITEM1", "ITEM2"]

    @staticmethod
    def test_run_specific_stages() -> None:
        """Test running only specific stages."""
        pipeline = Pipeline()
        _stage1 = ConcretePipelineStage()
        _stage2 = ConcretePipelineStage()

        # Give stages different names for testing
        class Stage1(ConcretePipelineStage):
            """First stage."""

            @property
            def stage_name(self) -> str:
                """Return stage name."""
                return "Stage 1"

        class Stage2(ConcretePipelineStage):
            """Second stage."""

            @property
            def stage_name(self) -> str:
                """Return stage name."""
                return "Stage 2"

        pipeline.add_stage(Stage1()).add_stage(Stage2())

        results = pipeline.run(stages=["Stage 1"])

        # Should only run Stage 1
        assert len(results) == 1
        assert "Stage 1" in results
        assert "Stage 2" not in results

    @staticmethod
    def test_run_stage_failure_raises() -> None:
        """Test that stage failure raises exception."""
        pipeline = Pipeline()
        stage = FailingStage()

        pipeline.add_stage(stage)

        with pytest.raises(RuntimeError, match="Load failed"):
            pipeline.run()
