"""Interactive demo for normalization strategies.

This script demonstrates the three normalization strategies available in the
analysis layer: MinMaxNormalizer, ZScoreNormalizer, and RobustNormalizer.
Shows edge cases, algorithm differences, and when to use each strategy.

Requirements:
    - No external dependencies or setup required
    - Uses synthetic examples with various edge cases

Usage:
    python _demos/sandbox_normalizers_demo.py
"""

# Local
from msc.analysis.normalizers import MinMaxNormalizer, RobustNormalizer, ZScoreNormalizer


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


def print_normalization_results(
        values: list[float],
        results: dict[str, list[float]],
) -> None:
    """Print normalization results in a formatted table.

    Args:
        values: Original values
        results: Dictionary of normalizer name -> normalized values
    """
    print(f"Original values: {values}")
    print()
    for name, normalized in results.items():
        formatted = [f"{v:.3f}" for v in normalized]
        print(f"{name:20s}: {formatted}")
    print()


def demo_basic_normalization() -> None:
    """Demonstrate basic normalization with typical data."""
    print_separator("Basic Normalization")

    values = [10.0, 20.0, 30.0, 40.0, 50.0]

    minmax = MinMaxNormalizer()
    zscore = ZScoreNormalizer()
    robust = RobustNormalizer()

    results = {
        "MinMax (0-1)": minmax.normalize(values),
        "Z-Score": zscore.normalize(values),
        "Robust (IQR)": robust.normalize(values),
    }

    print("Normalizing evenly distributed values:")
    print_normalization_results(values, results)

    print("MinMax: Scales to [0, 1] range (min=0, max=1)")
    print("Z-Score: Centers around 0 with unit variance")
    print("Robust: Uses median and IQR, resistant to outliers")


def demo_with_outliers() -> None:
    """Demonstrate normalization with outliers."""
    print_separator("Handling Outliers")

    # Data with extreme outlier
    values = [10.0, 12.0, 11.0, 13.0, 100.0]

    minmax = MinMaxNormalizer()
    zscore = ZScoreNormalizer()
    robust = RobustNormalizer()

    results = {
        "MinMax (0-1)": minmax.normalize(values),
        "Z-Score": zscore.normalize(values),
        "Robust (IQR)": robust.normalize(values),
    }

    print("Normalizing data with outlier (100.0):")
    print_normalization_results(values, results)

    print("MinMax: Outlier becomes 1.0, compresses other values near 0")
    print("Z-Score: Outlier gets high z-score, other values near 0")
    print("Robust: Best handles outliers using median/IQR (recommended)")


def demo_edge_cases() -> None:
    """Demonstrate edge case handling."""
    print_separator("Edge Cases")

    minmax = MinMaxNormalizer()
    zscore = ZScoreNormalizer()
    robust = RobustNormalizer()

    # Edge case 1: All same values
    print("1. All same values [5.0, 5.0, 5.0]:")
    values = [5.0, 5.0, 5.0]
    print(f"   MinMax: {minmax.normalize(values)}")
    print(f"   Z-Score: {zscore.normalize(values)}")
    print(f"   Robust: {robust.normalize(values)}")
    print("   → All return [0.5, 0.5, 0.5] (midpoint)")
    print()

    # Edge case 2: Single value
    print("2. Single value [42.0]:")
    values = [42.0]
    print(f"   MinMax: {minmax.normalize(values)}")
    print(f"   Z-Score: {zscore.normalize(values)}")
    print(f"   Robust: {robust.normalize(values)}")
    print("   → All return [0.5] (midpoint)")
    print()

    # Edge case 3: Empty list
    print("3. Empty list []:")
    values: list[float] = []
    print(f"   MinMax: {minmax.normalize(values)}")
    print(f"   Z-Score: {zscore.normalize(values)}")
    print(f"   Robust: {robust.normalize(values)}")
    print("   → All return [] (empty list)")
    print()

    # Edge case 4: Two identical values
    print("4. Two identical values [10.0, 10.0]:")
    values = [10.0, 10.0]
    print(f"   MinMax: {minmax.normalize(values)}")
    print(f"   Z-Score: {zscore.normalize(values)}")
    print(f"   Robust: {robust.normalize(values)}")
    print("   → All return [0.5, 0.5] (midpoint)")


def demo_with_negatives() -> None:
    """Demonstrate normalization with negative values."""
    print_separator("Negative Values")

    values = [-50.0, -25.0, 0.0, 25.0, 50.0]

    minmax = MinMaxNormalizer()
    zscore = ZScoreNormalizer()
    robust = RobustNormalizer()

    results = {
        "MinMax (0-1)": minmax.normalize(values),
        "Z-Score": zscore.normalize(values),
        "Robust (IQR)": robust.normalize(values),
    }

    print("Normalizing values with negatives:")
    print_normalization_results(values, results)

    print("All normalizers handle negative values correctly")
    print("MinMax: Still scales to [0, 1], -50 → 0, 50 → 1")


def demo_zero_variance() -> None:
    """Demonstrate zero variance handling."""
    print_separator("Zero Variance Data")

    values = [7.0, 7.0, 7.0, 7.0, 7.0]

    minmax = MinMaxNormalizer()
    zscore = ZScoreNormalizer()
    robust = RobustNormalizer()

    print("Data with zero variance (all values = 7.0):")
    print(f"MinMax result: {minmax.normalize(values)}")
    print(f"Z-Score result: {zscore.normalize(values)}")
    print(f"Robust result: {robust.normalize(values)}")
    print()
    print("All normalizers return [0.5, 0.5, 0.5, 0.5, 0.5]")
    print("This prevents division by zero and returns neutral values")


def demo_skewed_distribution() -> None:
    """Demonstrate normalization with skewed distribution."""
    print_separator("Skewed Distribution")

    # Right-skewed data (most values low, few high)
    values = [1.0, 2.0, 3.0, 4.0, 5.0, 50.0, 100.0]

    minmax = MinMaxNormalizer()
    zscore = ZScoreNormalizer()
    robust = RobustNormalizer()

    results = {
        "MinMax (0-1)": minmax.normalize(values),
        "Z-Score (clipped)": zscore.normalize(values),
        "Robust (IQR)": robust.normalize(values),
    }

    print("Normalizing right-skewed distribution:")
    print_normalization_results(values, results)

    print("Robust normalizer is best for skewed data:")
    print("- Uses median instead of mean (less affected by skew)")
    print("- Uses IQR instead of std dev (more stable)")
    print("- Recommended for real-world music metrics (often skewed)")


def demo_algorithm_comparison() -> None:
    """Compare all three normalization algorithms."""
    print_separator("Algorithm Comparison")

    # Typical music streaming data (skewed, with outliers)
    spotify_streams = [100_000, 250_000, 500_000, 750_000, 1_000_000, 5_000_000]

    minmax = MinMaxNormalizer()
    zscore = ZScoreNormalizer()
    robust = RobustNormalizer()

    results = {
        "MinMax": minmax.normalize(spotify_streams),
        "Z-Score": zscore.normalize(spotify_streams),
        "Robust": robust.normalize(spotify_streams),
    }

    print("Normalizing Spotify streams (typical music data):")
    print_normalization_results(spotify_streams, results)

    print("When to use each:")
    print()
    print("✓ MinMax:")
    print("  - Simple, interpretable (0 = min, 1 = max)")
    print("  - Good for well-behaved data without outliers")
    print("  - DEFAULT for PowerRankingScorer")
    print()
    print("✓ Z-Score:")
    print("  - Good for normally distributed data")
    print("  - Preserves distribution shape")
    print("  - Clips to [-3, 3] to prevent extreme values")
    print()
    print("✓ Robust:")
    print("  - Best for skewed data with outliers")
    print("  - Uses median/IQR instead of mean/std")
    print("  - Recommended for real-world music metrics")


def demo_manual_scaling() -> None:
    """Demonstrate manual scaling after normalization."""
    print_separator("Manual Scaling After Normalization")

    values = [10.0, 20.0, 30.0, 40.0, 50.0]

    # Normalize to [0, 1]
    minmax = MinMaxNormalizer()
    normalized = minmax.normalize(values)

    print("Normalize then scale manually:")
    print(f"Original: {values}")
    print(f"MinMax [0, 1]: {[f'{v:.3f}' for v in normalized]}")
    print()

    # Scale to [0, 100] manually
    scaled_100 = [v * 100 for v in normalized]
    print(f"Scaled to [0, 100]: {[f'{v:.1f}' for v in scaled_100]}")
    print()

    # Scale to [1, 5] manually
    scaled_5 = [1 + (v * 4) for v in normalized]
    print(f"Scaled to [1, 5]: {[f'{v:.2f}' for v in scaled_5]}")
    print()

    print("Manual scaling useful for:")
    print("- Percentage scores (multiply by 100)")
    print("- Rating scales (scale to 1-5, 0-10)")
    print("- UI display purposes")


def main() -> None:
    """Run all normalization strategy demos."""
    print("=" * 80)
    print(" Normalization Strategies - Interactive Demo")
    print("=" * 80)

    demo_basic_normalization()
    demo_with_outliers()
    demo_edge_cases()
    demo_with_negatives()
    demo_zero_variance()
    demo_skewed_distribution()
    demo_algorithm_comparison()
    demo_manual_scaling()

    print_separator()
    print("✓ All demos completed successfully!")
    print()
    print("Key Takeaways:")
    print("1. MinMax: Simple [0,1] scaling, sensitive to outliers (DEFAULT)")
    print("2. Z-Score: Standardization around mean, for normal distributions")
    print("3. Robust: Median/IQR based, best for skewed real-world data")
    print()


if __name__ == "__main__":
    main()
