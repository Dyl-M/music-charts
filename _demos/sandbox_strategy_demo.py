"""Interactive demo for the Strategy Pattern in the analysis layer.

This script demonstrates the Strategy Pattern implementation, showing how to:
- Swap normalization strategies without changing client code
- Create custom normalization strategies
- Use dependency injection for flexible algorithm selection
- Benefit from the Open/Closed Principle

Requirements:
    - No external dependencies or setup required
    - Uses synthetic examples to demonstrate the pattern

Usage:
    python _demos/sandbox_strategy_demo.py
"""

# Standard library
from typing import Any

# Local
from msc.analysis.normalizers import MinMaxNormalizer, RobustNormalizer, ZScoreNormalizer
from msc.analysis.strategy import NormalizationStrategy


def print_separator(title: str = "") -> None:
    """Print a formatted separator line.

    Args:
        title: Optional title to display in separator.
    """
    if title:
        print(f"\n{'=' * 80}")
        print(f" {title}")
        print(f"{'=' * 80}\n")
    else:
        print(f"{'=' * 80}\n")


class DataProcessor:
    """Example client class that uses normalization strategies.

    Demonstrates dependency injection and strategy swapping.
    """

    def __init__(self, strategy: NormalizationStrategy) -> None:
        """Initialize processor with a normalization strategy.

        Args:
            strategy: Normalization strategy to use
        """
        self.strategy = strategy

    def process_data(self, values: list[float]) -> list[float]:
        """Process data using the configured strategy.

        Args:
            values: Values to normalize

        Returns:
            Normalized values
        """
        return self.strategy.normalize(values)

    def set_strategy(self, strategy: NormalizationStrategy) -> None:
        """Change the normalization strategy at runtime.

        Args:
            strategy: New normalization strategy
        """
        self.strategy = strategy


def demo_strategy_swapping() -> None:
    """Demonstrate swapping strategies at runtime."""
    print_separator("Strategy Swapping (Runtime Flexibility)")

    data = [10.0, 20.0, 30.0, 40.0, 50.0]

    # Create processor with MinMax strategy
    processor = DataProcessor(MinMaxNormalizer())

    print("Same data, different strategies:")
    print(f"Original data: {data}")
    print()

    # Use MinMax
    result = processor.process_data(data)
    print(f"MinMax strategy:  {[f'{v:.3f}' for v in result]}")

    # Swap to Z-Score
    processor.set_strategy(ZScoreNormalizer())
    result = processor.process_data(data)
    print(f"Z-Score strategy: {[f'{v:.3f}' for v in result]}")

    # Swap to Robust
    processor.set_strategy(RobustNormalizer())
    result = processor.process_data(data)
    print(f"Robust strategy:  {[f'{v:.3f}' for v in result]}")

    print()
    print("✓ Strategy changed without modifying DataProcessor code")
    print("✓ This is the Strategy Pattern in action!")


def demo_dependency_injection() -> None:
    """Demonstrate dependency injection with strategies."""
    print_separator("Dependency Injection")

    data = [100.0, 200.0, 300.0, 400.0, 500.0]

    # Different processors with different strategies
    processors = {
        "MinMax Processor": DataProcessor(MinMaxNormalizer()),
        "Z-Score Processor": DataProcessor(ZScoreNormalizer()),
        "Robust Processor": DataProcessor(RobustNormalizer()),
    }

    print("Multiple processors, each with different strategy:")
    print(f"Data: {data}")
    print()

    for name, processor in processors.items():
        result = processor.process_data(data)
        formatted = [f"{v:.3f}" for v in result]
        print(f"{name:20s}: {formatted}")

    print()
    print("✓ Each processor has its own strategy (injected at creation)")
    print("✓ Strategies are interchangeable (same interface)")


class LogarithmicNormalizer(NormalizationStrategy):
    """Custom normalization strategy using logarithmic scaling.

    Useful for highly skewed data (e.g., follower counts, view counts).
    """

    def get_name(self) -> str:
        """Get strategy name."""
        return "Logarithmic"

    def normalize(self, values: list[float]) -> list[float]:
        """Normalize using log scaling then MinMax.

        Args:
            values: Values to normalize

        Returns:
            Log-scaled and normalized values [0, 1]
        """
        import math

        if not values:
            return []

        if len(values) == 1:
            return [0.5]

        # Apply log transform (add 1 to handle zeros)
        log_values = [math.log(v + 1) for v in values]

        # Then apply MinMax normalization
        min_val = min(log_values)
        max_val = max(log_values)

        if max_val == min_val:
            return [0.5] * len(log_values)

        return [(v - min_val) / (max_val - min_val) for v in log_values]


class PercentileNormalizer(NormalizationStrategy):
    """Custom normalization strategy using percentile ranking.

    Converts values to their percentile rank (0-1 scale).
    """

    def get_name(self) -> str:
        """Get strategy name."""
        return "Percentile"

    def normalize(self, values: list[float]) -> list[float]:
        """Normalize using percentile ranking.

        Args:
            values: Values to normalize

        Returns:
            Percentile ranks [0, 1]
        """
        if not values:
            return []

        if len(values) == 1:
            return [0.5]

        # Sort values to get ranks
        sorted_values = sorted(values)
        n = len(values)

        # Convert to percentile rank
        return [(sorted_values.index(v) + 1) / n for v in values]


def demo_custom_strategies() -> None:
    """Demonstrate creating and using custom strategies."""
    print_separator("Custom Normalization Strategies")

    # Highly skewed data (typical for social media metrics)
    data = [100, 500, 1_000, 10_000, 1_000_000]

    print("Data: Social media follower counts (highly skewed)")
    print(f"Values: {data}")
    print()

    # Built-in strategies
    minmax = DataProcessor(MinMaxNormalizer())
    robust = DataProcessor(RobustNormalizer())

    # Custom strategies
    log_norm = DataProcessor(LogarithmicNormalizer())
    percentile = DataProcessor(PercentileNormalizer())

    print("Built-in strategies:")
    print(f"  MinMax:     {[f'{v:.3f}' for v in minmax.process_data(data)]}")
    print(f"  Robust:     {[f'{v:.3f}' for v in robust.process_data(data)]}")
    print()

    print("Custom strategies:")
    print(f"  Logarithmic: {[f'{v:.3f}' for v in log_norm.process_data(data)]}")
    print(f"  Percentile:  {[f'{v:.3f}' for v in percentile.process_data(data)]}")
    print()

    print("✓ Custom strategies implement NormalizationStrategy interface")
    print("✓ They work seamlessly with existing code (polymorphism)")


def demo_strategy_selection() -> None:
    """Demonstrate strategy selection based on data characteristics."""
    print_separator("Intelligent Strategy Selection")

    def select_strategy(values: list[float]) -> NormalizationStrategy:
        """Select appropriate strategy based on data characteristics.

        Args:
            values: Data to analyze

        Returns:
            Recommended normalization strategy
        """
        if not values or len(values) < 2:
            return MinMaxNormalizer()

        # Calculate skewness (simplified)
        mean = sum(values) / len(values)
        median = sorted(values)[len(values) // 2]
        skew = abs(mean - median) / (max(values) - min(values) + 1e-10)

        # Check for outliers
        sorted_vals = sorted(values)
        q1 = sorted_vals[len(sorted_vals) // 4]
        q3 = sorted_vals[3 * len(sorted_vals) // 4]
        iqr = q3 - q1
        outliers = [v for v in values if v < q1 - 1.5 * iqr or v > q3 + 1.5 * iqr]

        # Select strategy
        if len(outliers) > 0:
            print("  → Detected outliers → Using Robust strategy")
            return RobustNormalizer()

        if skew > 0.3:
            print("  → Detected skewness → Using Robust strategy")
            return RobustNormalizer()

        print("  → Well-behaved data → Using MinMax strategy")
        return MinMaxNormalizer()

    # Test different datasets
    datasets = {
        "Normal distribution": [10.0, 15.0, 20.0, 25.0, 30.0],
        "With outliers": [10.0, 12.0, 11.0, 13.0, 100.0],
        "Right-skewed": [1.0, 2.0, 3.0, 4.0, 50.0, 100.0],
    }

    for name, data in datasets.items():
        print(f"\n{name}: {data}")
        strategy = select_strategy(data)
        processor = DataProcessor(strategy)
        result = processor.process_data(data)
        print(f"  Result: {[f'{v:.3f}' for v in result]}")

    print()
    print("✓ Strategy selection can be automated based on data characteristics")
    print("✓ Encapsulation: Client code doesn't need to know algorithm details")


def demo_open_closed_principle() -> None:
    """Demonstrate Open/Closed Principle with strategies."""
    print_separator("Open/Closed Principle")

    print("The Strategy Pattern supports the Open/Closed Principle:")
    print()
    print("✓ OPEN for extension:")
    print("  - Add new strategies (LogarithmicNormalizer, PercentileNormalizer)")
    print("  - No changes to existing code (NormalizationStrategy interface)")
    print()
    print("✓ CLOSED for modification:")
    print("  - DataProcessor doesn't change when adding new strategies")
    print("  - Existing strategies remain unchanged")
    print()
    print("Example:")
    print("  1. Create new class implementing NormalizationStrategy")
    print("  2. Inject it into DataProcessor")
    print("  3. Works immediately without changing any existing code!")
    print()

    # Demonstrate
    class SquareRootNormalizer(NormalizationStrategy):
        """Another custom strategy (square root transformation)."""

        def get_name(self) -> str:
            """Get strategy name."""
            return "SquareRoot"

        def normalize(self, values: list[float]) -> list[float]:
            """Normalize using square root transformation."""
            import math

            if not values or len(values) == 1:
                return [0.5] * len(values)

            # Apply square root
            sqrt_values = [math.sqrt(v) if v >= 0 else 0 for v in values]

            # Then MinMax
            min_val, max_val = min(sqrt_values), max(sqrt_values)
            if max_val == min_val:
                return [0.5] * len(sqrt_values)

            return [(v - min_val) / (max_val - min_val) for v in sqrt_values]

    data = [1.0, 4.0, 9.0, 16.0, 25.0]
    processor = DataProcessor(SquareRootNormalizer())
    result = processor.process_data(data)

    print(f"New SquareRootNormalizer: {data} → {[f'{v:.3f}' for v in result]}")
    print("✓ Added without modifying DataProcessor or other strategies!")


def demo_real_world_usage() -> None:
    """Demonstrate real-world usage in PowerRankingScorer context."""
    print_separator("Real-World Usage: PowerRankingScorer")

    print("In the music-charts pipeline:")
    print()
    print("1. PowerRankingScorer accepts a NormalizationStrategy:")
    print("   scorer = PowerRankingScorer(normalizer=MinMaxNormalizer())")
    print()
    print("2. For different use cases, swap strategies:")
    print("   - MinMax: Default, simple interpretation")
    print("   - Robust: Better for real-world music metrics (skewed data)")
    print("   - Z-Score: If you want standardized scores")
    print()
    print("3. Change strategy without touching scorer code:")
    print("   scorer.normalizer = RobustNormalizer()  # Switch at runtime")
    print()
    print("4. Test results with different strategies:")
    print("   - Compare rankings with MinMax vs Robust")
    print("   - Choose best strategy for your data")
    print()
    print("Benefits:")
    print("✓ Flexible: Easy to experiment with different algorithms")
    print("✓ Testable: Mock strategies for unit tests")
    print("✓ Maintainable: Clear separation of concerns")
    print("✓ Extensible: Add new strategies without breaking changes")


def main() -> None:
    """Run all strategy pattern demos."""
    print("=" * 80)
    print(" Strategy Pattern - Interactive Demo")
    print("=" * 80)

    demo_strategy_swapping()
    demo_dependency_injection()
    demo_custom_strategies()
    demo_strategy_selection()
    demo_open_closed_principle()
    demo_real_world_usage()

    print_separator()
    print("✓ All demos completed successfully!")
    print()
    print("Key Takeaways:")
    print("1. Strategy Pattern enables runtime algorithm swapping")
    print("2. Dependency injection makes code flexible and testable")
    print("3. Custom strategies extend functionality without modification")
    print("4. Supports SOLID principles (Open/Closed, Dependency Inversion)")
    print("5. Used by PowerRankingScorer for pluggable normalization")
    print()


if __name__ == "__main__":
    main()
