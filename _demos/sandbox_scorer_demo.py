"""Interactive demo for PowerRankingScorer.

This script demonstrates the PowerRankingScorer which computes power rankings
from enriched track data using category-based scoring, normalization, and
weighted aggregation.

Requirements:
    - Requires _config/categories.json to be present
    - Uses synthetic track data for demonstration

Usage:
    python _demos/sandbox_scorer_demo.py
"""

# Standard library
from pathlib import Path

# Local
from msc.analysis.normalizers import MinMaxNormalizer, RobustNormalizer
from msc.analysis.scorer import PowerRankingScorer
from msc.models.platforms import (
    AmazonMusicStats,
    AppleMusicStats,
    BeatportStats,
    DeezerStats,
    SoundCloudStats,
    SpotifyStats,
    TidalStats,
    TikTokStats,
    TracklistsStats,
    YouTubeStats,
)
from msc.models.stats import PlatformStats, TrackWithStats
from msc.models.track import SongstatsIdentifiers, Track


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


def create_sample_track(
        title: str,
        artist: str,
        spotify_streams: int = 0,
        spotify_popularity: int = 0,
        youtube_views: int = 0,
        tiktok_views: int = 0,
) -> TrackWithStats:
    """Create a sample track with platform stats for testing.

    Args:
        title: Track title
        artist: Artist name
        spotify_streams: Spotify stream count
        spotify_popularity: Spotify popularity peak
        youtube_views: YouTube video views
        tiktok_views: TikTok views

    Returns:
        TrackWithStats instance
    """
    track = Track(
        title=title,
        artist_list=[artist],
        year=2025,
        songstats_identifiers=SongstatsIdentifiers(
            songstats_id=f"id_{title.lower().replace(' ', '_')}",
            songstats_title=title,
        ),
    )

    platform_stats = PlatformStats(
        spotify=SpotifyStats(
            streams_total=spotify_streams,
            popularity_peak=spotify_popularity,
            playlists_editorial_total=10,
            playlist_reach_total=100000,
        ),
        youtube=YouTubeStats(
            video_views_total=youtube_views,
            charts_total=5,
            engagement_rate_total=0.05,
        ),
        tiktok=TikTokStats(
            views_total=tiktok_views,
            engagement_rate_total=0.08,
        ),
        deezer=DeezerStats(popularity_peak=max(0, spotify_popularity - 10)),
        apple_music=AppleMusicStats(),
        soundcloud=SoundCloudStats(),
        tidal=TidalStats(),
        amazon_music=AmazonMusicStats(),
        beatport=BeatportStats(),
        tracklists=TracklistsStats(),
    )

    return TrackWithStats(
        track=track,
        songstats_identifiers=track.songstats_identifiers,
        platform_stats=platform_stats,
    )


def demo_basic_scoring() -> None:
    """Demonstrate basic power ranking computation."""
    print_separator("Basic Power Ranking Computation")

    # Create sample tracks with different performance levels
    tracks = [
        create_sample_track(
            "Viral Hit",
            "DJ Famous",
            spotify_streams=10_000_000,
            spotify_popularity=95,
            youtube_views=50_000_000,
            tiktok_views=100_000_000,
        ),
        create_sample_track(
            "Underground Gem",
            "Producer Unknown",
            spotify_streams=500_000,
            spotify_popularity=65,
            youtube_views=1_000_000,
            tiktok_views=5_000_000,
        ),
        create_sample_track(
            "Moderate Success",
            "Artist Rising",
            spotify_streams=2_000_000,
            spotify_popularity=78,
            youtube_views=10_000_000,
            tiktok_views=20_000_000,
        ),
    ]

    # Create scorer with default settings
    scorer = PowerRankingScorer()

    # Compute rankings
    results = scorer.compute_rankings(tracks)

    print(f"Computed rankings for {results.total_tracks} tracks:")
    print()

    for ranking in results.rankings:
        print(f"Rank #{ranking.rank}: {ranking.track.title} - {ranking.artist_display}")
        print(f"  Total Score: {ranking.total_score:.4f}")
        print(f"  Top Categories:")

        # Show top 3 category scores
        sorted_categories = sorted(
            ranking.category_scores,
            key=lambda x: x.weighted_score,
            reverse=True,
        )

        for cat_score in sorted_categories[:3]:
            print(
                f"    - {cat_score.category}: "
                f"{cat_score.weighted_score:.4f} "
                f"(weight={cat_score.weight})"
            )

        print()

    print("✓ Tracks ranked by total power score")
    print("✓ Higher streams/views = higher rank")


def demo_category_breakdown() -> None:
    """Demonstrate category-based scoring breakdown."""
    print_separator("Category Score Breakdown")

    # Create one track to analyze
    track = create_sample_track(
        "Test Track",
        "Test Artist",
        spotify_streams=5_000_000,
        spotify_popularity=85,
        youtube_views=25_000_000,
        tiktok_views=50_000_000,
    )

    scorer = PowerRankingScorer()
    results = scorer.compute_rankings([track])
    ranking = results.rankings[0]

    print(f"Track: {ranking.track.title}")
    print(f"Total Score: {ranking.total_score:.4f}")
    print()
    print("Category Breakdown:")
    print(f"{'Category':<25} {'Raw':<10} {'Weight':<8} {'Weighted':<10}")
    print("-" * 60)

    for cat_score in sorted(
            ranking.category_scores,
            key=lambda x: x.category,
    ):
        print(
            f"{cat_score.category:<25} "
            f"{cat_score.raw_score:>8.4f}  "
            f"{cat_score.weight:>6d}  "
            f"{cat_score.weighted_score:>8.4f}"
        )

    print()
    print("Scoring process:")
    print("1. Extract metrics for each category from platform stats")
    print("2. Normalize raw scores to [0, 1] range (MinMax by default)")
    print("3. Apply category weight (1=Negligible, 2=Low, 4=High)")
    print("4. Sum weighted scores for total power score")


def demo_weighting_system() -> None:
    """Demonstrate the category weighting system."""
    print_separator("Category Weighting System")

    print("Category weights (from msc/config/constants.py):")
    print()

    weights = {
        "charts": 1,
        "engagement": 1,
        "shorts": 1,
        "reach": 2,
        "playlists": 2,
        "professional_support": 2,
        "popularity": 4,
        "streams": 4,
    }

    print("Negligible (×1):")
    for cat, weight in weights.items():
        if weight == 1:
            print(f"  • {cat}")

    print()
    print("Low (×2):")
    for cat, weight in weights.items():
        if weight == 2:
            print(f"  • {cat}")

    print()
    print("High (×4):")
    for cat, weight in weights.items():
        if weight == 4:
            print(f"  • {cat}")

    print()
    print("Impact on final score:")
    print("- High-weight categories (streams, popularity) matter 4× more")
    print("- Low-weight categories (playlists, reach) matter 2× more")
    print("- Negligible categories (charts, engagement) have base weight")


def demo_normalization_strategies() -> None:
    """Demonstrate different normalization strategies."""
    print_separator("Normalization Strategy Comparison")

    # Create tracks with one outlier
    tracks = [
        create_sample_track("Track 1", "Artist A", spotify_streams=1_000_000),
        create_sample_track("Track 2", "Artist B", spotify_streams=2_000_000),
        create_sample_track("Track 3", "Artist C", spotify_streams=3_000_000),
        create_sample_track("Viral Track", "Artist D", spotify_streams=50_000_000),
    ]

    # Score with MinMax (default)
    scorer_minmax = PowerRankingScorer(normalizer=MinMaxNormalizer())
    results_minmax = scorer_minmax.compute_rankings(tracks)

    # Score with Robust (better for outliers)
    scorer_robust = PowerRankingScorer(normalizer=RobustNormalizer())
    results_robust = scorer_robust.compute_rankings(tracks)

    print("Rankings with MinMax normalization:")
    for ranking in results_minmax.rankings:
        print(f"  #{ranking.rank}: {ranking.track.title} ({ranking.total_score:.4f})")

    print()
    print("Rankings with Robust normalization:")
    for ranking in results_robust.rankings:
        print(f"  #{ranking.rank}: {ranking.track.title} ({ranking.total_score:.4f})")

    print()
    print("Notice:")
    print("- MinMax: Outlier (Viral Track) dominates, compresses other scores")
    print("- Robust: Uses median/IQR, less affected by outlier")
    print("- Choose Robust for real-world data with outliers (recommended)")


def demo_data_availability() -> None:
    """Demonstrate data availability impact on scoring."""
    print_separator("Data Availability Impact")

    # Track with complete data
    complete_track = create_sample_track(
        "Complete Data",
        "Artist X",
        spotify_streams=5_000_000,
        spotify_popularity=80,
        youtube_views=10_000_000,
        tiktok_views=20_000_000,
    )

    # Track with partial data (missing YouTube and TikTok)
    partial_track = create_sample_track(
        "Partial Data",
        "Artist Y",
        spotify_streams=5_000_000,
        spotify_popularity=80,
        youtube_views=0,  # Missing
        tiktok_views=0,  # Missing
    )

    scorer = PowerRankingScorer()
    results = scorer.compute_rankings([complete_track, partial_track])

    print("Comparing tracks with same Spotify stats:")
    print()

    for ranking in results.rankings:
        print(f"{ranking.track.title}:")
        print(f"  Total Score: {ranking.total_score:.4f}")

        # Calculate data availability
        total_categories = len(ranking.category_scores)
        categories_with_data = sum(
            1 for cat in ranking.category_scores if cat.raw_score > 0
        )
        availability = categories_with_data / total_categories

        print(f"  Data Availability: {availability:.1%}")
        print()

    print("Data availability affects scoring:")
    print("- More complete data → higher potential score")
    print("- Missing data = 0 for those metrics")
    print("- Incentivizes comprehensive data collection")


def demo_category_configuration() -> None:
    """Demonstrate category configuration from JSON."""
    print_separator("Category Configuration")

    config_path = Path("_config/categories.json")

    print(f"Categories loaded from: {config_path}")
    print()

    scorer = PowerRankingScorer()
    print(f"Loaded {len(scorer.category_config)} categories:")
    print()

    for category, metrics in sorted(scorer.category_config.items()):
        print(f"{category} ({len(metrics)} metrics):")
        for metric in sorted(metrics):
            print(f"  - {metric}")
        print()

    print("✓ Configuration is user-editable")
    print("✓ Add/remove metrics to customize scoring")
    print("✓ Useful for different music genres or use cases")


def demo_filtering_and_sorting() -> None:
    """Demonstrate result filtering and sorting."""
    print_separator("Result Filtering and Sorting")

    # Create diverse tracks
    tracks = [
        create_sample_track("Mega Hit", "Artist A", spotify_streams=20_000_000),
        create_sample_track("Big Hit", "Artist B", spotify_streams=10_000_000),
        create_sample_track("Medium Hit", "Artist C", spotify_streams=5_000_000),
        create_sample_track("Small Hit", "Artist D", spotify_streams=1_000_000),
        create_sample_track("Indie Track", "Artist E", spotify_streams=100_000),
    ]

    scorer = PowerRankingScorer()
    results = scorer.compute_rankings(tracks)

    # Top 3 (using list slicing)
    print("Top 3 tracks:")
    top_3 = results.rankings[:3]
    for ranking in top_3:
        print(f"  #{ranking.rank}: {ranking.track.title} ({ranking.total_score:.4f})")

    print()

    # Filter by minimum score (manual filtering)
    min_score = 0.5
    print(f"Tracks with score ≥ {min_score}:")
    filtered = [r for r in results.rankings if r.total_score >= min_score]
    for ranking in filtered:
        print(f"  #{ranking.rank}: {ranking.track.title} ({ranking.total_score:.4f})")

    print()

    # Get rank range (using list slicing, ranks 2-4 means indices 1-4)
    print("Ranks 2-4:")
    middle_ranks = results.rankings[1:4]
    for ranking in middle_ranks:
        print(f"  #{ranking.rank}: {ranking.track.title} ({ranking.total_score:.4f})")

    print()
    print("✓ PowerRankingResults.rankings provides list of rankings")
    print("✓ Use list slicing and filtering for Top 10, Top 100, etc.")


def main() -> None:
    """Run all PowerRankingScorer demos."""
    print("=" * 80)
    print(" PowerRankingScorer - Interactive Demo")
    print("=" * 80)

    demo_basic_scoring()
    demo_category_breakdown()
    demo_weighting_system()
    demo_normalization_strategies()
    demo_data_availability()
    demo_category_configuration()
    demo_filtering_and_sorting()

    print_separator()
    print("✓ All demos completed successfully!")
    print()
    print("Key Takeaways:")
    print("1. PowerRankingScorer uses category-based weighted scoring")
    print("2. Normalization ensures fair comparison across metrics")
    print("3. Weighting system (1/2/4) emphasizes important categories")
    print("4. Normalization strategy is swappable (Strategy pattern)")
    print("5. Categories are configurable via _config/categories.json")
    print("6. Data availability impacts final scores")
    print()


if __name__ == "__main__":
    main()
