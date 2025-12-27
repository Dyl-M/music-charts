"""Unit tests for strategy interfaces.

Tests abstract NormalizationStrategy, ScoringStrategy, and WeightingStrategy.
"""
from abc import ABC

# Third-party
import pytest

# Local
from msc.analysis.strategy import (
    NormalizationStrategy,
    ScoringStrategy,
    WeightingStrategy,
)


class TestNormalizationStrategyInterface:
    """Tests for abstract NormalizationStrategy interface."""

    @staticmethod
    def test_cannot_instantiate_directly() -> None:
        """Should not allow direct instantiation."""
        with pytest.raises(TypeError, match="abstract"):
            # noinspection PyAbstractClass
            NormalizationStrategy()  # skipcq: PYL-E0110

    @staticmethod
    def test_normalize_is_abstract() -> None:
        """Should require normalize method implementation."""

        class IncompleteStrategy(NormalizationStrategy, ABC):
            """Strategy missing normalize method."""

            def get_name(self) -> str:
                """Return strategy name."""
                return "Incomplete"

        with pytest.raises(TypeError, match="normalize"):
            # noinspection PyAbstractClass
            IncompleteStrategy()  # skipcq: PYL-E0110

    @staticmethod
    def test_get_name_is_abstract() -> None:
        """Should require get_name method implementation."""

        class IncompleteStrategy(NormalizationStrategy, ABC):
            """Strategy missing get_name method."""

            def normalize(self, values: list[float]) -> list[float]:
                """Normalize input values."""
                return values

        with pytest.raises(TypeError, match="get_name"):
            # noinspection PyAbstractClass
            IncompleteStrategy()  # skipcq: PYL-E0110


class TestScoringStrategyInterface:
    """Tests for abstract ScoringStrategy interface."""

    @staticmethod
    def test_cannot_instantiate_directly() -> None:
        """Should not allow direct instantiation."""
        with pytest.raises(TypeError, match="abstract"):
            # noinspection PyAbstractClass
            ScoringStrategy()  # skipcq: PYL-E0110

    @staticmethod
    def test_compute_category_scores_is_abstract() -> None:
        """Should require compute_category_scores method implementation."""

        class IncompleteStrategy(ScoringStrategy, ABC):
            """Strategy missing compute_category_scores method."""

            def compute_power_ranking(self, track, category_scores, weights):
                """Compute power ranking."""
                raise NotImplementedError()

            def get_name(self) -> str:
                """Return strategy name."""
                return "Incomplete"

        with pytest.raises(TypeError, match="compute_category_scores"):
            # noinspection PyAbstractClass
            IncompleteStrategy()  # skipcq: PYL-E0110

    @staticmethod
    def test_compute_power_ranking_is_abstract() -> None:
        """Should require compute_power_ranking method implementation."""

        class IncompleteStrategy(ScoringStrategy, ABC):
            """Strategy missing compute_power_ranking method."""

            def compute_category_scores(self, tracks, category_config):
                """Compute category scores."""
                return {}

            def get_name(self) -> str:
                """Return strategy name."""
                return "Incomplete"

        with pytest.raises(TypeError, match="compute_power_ranking"):
            # noinspection PyAbstractClass
            IncompleteStrategy()  # skipcq: PYL-E0110


class TestWeightingStrategyInterface:
    """Tests for abstract WeightingStrategy interface."""

    @staticmethod
    def test_cannot_instantiate_directly() -> None:
        """Should not allow direct instantiation."""
        with pytest.raises(TypeError, match="abstract"):
            # noinspection PyAbstractClass
            WeightingStrategy()  # skipcq: PYL-E0110

    @staticmethod
    def test_apply_weights_is_abstract() -> None:
        """Should require apply_weights method implementation."""

        class IncompleteStrategy(WeightingStrategy, ABC):
            """Strategy missing apply_weights method."""

            def get_name(self) -> str:
                """Return strategy name."""
                return "Incomplete"

        with pytest.raises(TypeError, match="apply_weights"):
            # noinspection PyAbstractClass
            IncompleteStrategy()  # skipcq: PYL-E0110

    @staticmethod
    def test_get_name_is_abstract() -> None:
        """Should require get_name method implementation."""

        class IncompleteStrategy(WeightingStrategy, ABC):
            """Strategy missing get_name method."""

            def apply_weights(self, category_scores, weights):
                """Apply weights to scores."""
                return 0.0

        with pytest.raises(TypeError, match="get_name"):
            # noinspection PyAbstractClass
            IncompleteStrategy()  # skipcq: PYL-E0110
