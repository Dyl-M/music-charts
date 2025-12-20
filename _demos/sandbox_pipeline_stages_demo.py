"""Interactive demo for Pipeline Stages (Extract, Enrich, Rank).

This script demonstrates the three main pipeline stages conceptually using
mock/simulated data (no real API calls required).

Requirements:
    - No external API credentials required
    - Uses simulated data for demonstration
    - Creates temporary files in _data/demo/

Usage:
    python _demos/sandbox_pipeline_stages_demo.py
"""

# Standard library
from pathlib import Path

# Local
from msc.analysis.scorer import PowerRankingScorer
from msc.models.platforms import SpotifyStats
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


def cleanup_demo_files() -> None:
    """Clean up demo files and directories."""
    demo_dir = Path("_data/demo")
    if demo_dir.exists():
        for file in demo_dir.glob("pipeline_*.json"):
            file.unlink()
        for file in demo_dir.glob("pipeline_*.csv"):
            file.unlink()
        if not any(demo_dir.iterdir()):
            demo_dir.rmdir()


def demo_extraction_stage_concept() -> None:
    """Demonstrate ExtractionStage concept."""
    print_separator("Stage 1: Extraction")

    print("ExtractionStage: MusicBee Library → Songstats ID Resolution")
    print()

    print("Responsibilities:")
    print("  1. Extract tracks from MusicBee playlist (by name or ID)")
    print("  2. Search Songstats API for each track's ID")
    print("  3. Handle checkpoint resumability (skip already processed)")
    print("  4. Add tracks without Songstats ID to manual review queue")
    print("  5. Save tracks to JSONTrackRepository")
    print()

    print("Input:")
    print("  • MusicBee library XML file")
    print("  • Playlist name (e.g., '✅ 2025 Selection')")
    print("  • Year filter (optional)")
    print()

    print("Process:")
    print("  1. find_playlist_by_name() → Get playlist ID")
    print("  2. get_playlist_tracks(playlist_id) → List of tracks")
    print("  3. For each track:")
    print("     a. Build search query (artist + title)")
    print("     b. songstats_client.search_track(query)")
    print("     c. If found: Update track with Songstats ID")
    print("     d. If not found: Add to manual review queue")
    print("     e. Mark as processed in checkpoint")
    print("     f. Save to repository")
    print()

    print("Output:")
    print("  • JSONTrackRepository with tracks + Songstats IDs")
    print("  • Checkpoint state (processed/failed IDs)")
    print("  • Manual review queue (tracks needing intervention)")
    print()

    # Show simulated example
    print("Example: Simulated extraction")
    print()

    tracks_found = 3
    tracks_not_found = 1

    print(f"  Extracted {tracks_found + tracks_not_found} tracks from playlist")
    print(f"  ✓ {tracks_found} tracks: Songstats ID found")
    print(f"  ✗ {tracks_not_found} track: No Songstats ID (added to manual review)")
    print()

    print("Resumability:")
    print("  • If pipeline crashes at track 50/100")
    print("  • Restart resumes from track 51 (checkpoint)")
    print("  • No wasted API calls!")


def demo_enrichment_stage_concept() -> None:
    """Demonstrate EnrichmentStage concept."""
    print_separator("Stage 2: Enrichment")

    print("EnrichmentStage: Fetch Comprehensive Platform Statistics")
    print()

    print("Responsibilities:")
    print("  1. Fetch platform statistics from Songstats API")
    print("  2. Fetch historical peaks (popularity metrics)")
    print("  3. Optionally fetch YouTube video data (quota-free via Songstats)")
    print("  4. Handle checkpoint resumability")
    print("  5. Convert to TrackWithStats models")
    print("  6. Save to JSONStatsRepository")
    print()

    print("Input:")
    print("  • list[Track] from ExtractionStage (with Songstats IDs)")
    print()

    print("Process:")
    print("  For each track with Songstats ID:")
    print("    1. get_platform_stats(songstats_id) → Platform statistics")
    print("       (Spotify, Apple Music, YouTube, TikTok, Deezer, etc.)")
    print("    2. get_historical_peaks(songstats_id) → Peak popularity")
    print("    3. get_youtube_videos(songstats_id) → YouTube data (optional)")
    print("    4. Combine into TrackWithStats model")
    print("    5. Mark as processed in checkpoint")
    print("    6. Save to repository")
    print()

    print("Output:")
    print("  • JSONStatsRepository with enriched tracks")
    print("  • Checkpoint state")
    print()

    # Show simulated example
    print("Example: Simulated enrichment")
    print()

    track = Track(
        title="Levels",
        artist_list=["avicii"],
        year=2011,
        songstats_identifiers=SongstatsIdentifiers(
            songstats_id="abc123",
            songstats_title="Levels",
        ),
    )

    platform_stats = PlatformStats(
        spotify=SpotifyStats(
            streams_total=500_000_000,
            popularity_peak=95,
            playlists_editorial_total=1500,
            playlist_reach_total=50_000_000,
        )
    )

    print(f"  Track: {track.title} by {track.primary_artist}")
    print(f"  Songstats ID: {track.songstats_identifiers.songstats_id}")
    print()
    print("  Fetched stats:")
    print(f"    Spotify streams: {platform_stats.spotify.streams_total:,}")
    print(f"    Spotify popularity peak: {platform_stats.spotify.popularity_peak}")
    print(f"    Editorial playlists: {platform_stats.spotify.playlists_editorial_total}")
    print()

    print("Quota-free YouTube data:")
    print("  • Uses Songstats API (no YouTube quota consumed)")
    print("  • Alternative to YouTubeClient for most use cases")


def demo_ranking_stage_concept() -> None:
    """Demonstrate RankingStage concept."""
    print_separator("Stage 3: Ranking")

    print("RankingStage: Compute Power Rankings from Enriched Tracks")
    print()

    print("Responsibilities:")
    print("  1. Compute power rankings using PowerRankingScorer")
    print("  2. Export results to JSON (nested and flat formats)")
    print("  3. Export results to CSV")
    print("  4. Create merged output file with all track data")
    print()

    print("Input:")
    print("  • list[TrackWithStats] from EnrichmentStage")
    print()

    print("Process:")
    print("  1. PowerRankingScorer.compute_rankings(tracks)")
    print("     a. Extract metrics for each category")
    print("     b. Normalize scores (MinMax by default)")
    print("     c. Apply category weights (1/2/4)")
    print("     d. Sum weighted scores")
    print("     e. Sort by total score")
    print("     f. Assign ranks")
    print("  2. Export to multiple formats:")
    print("     • power_rankings_2025.json (nested)")
    print("     • power_rankings_2025_flat.json (flat, legacy)")
    print("     • power_rankings_2025.csv (tabular)")
    print()

    print("Output:")
    print("  • PowerRankingResults model")
    print("  • Multiple export formats")
    print()

    # Show simulated example
    print("Example: Simulated ranking")
    print()

    # Create sample tracks
    tracks = []
    for i, (title, artist, streams) in enumerate(
            [
                ("Viral Hit", "Artist A", 50_000_000),
                ("Big Hit", "Artist B", 20_000_000),
                ("Medium Hit", "Artist C", 5_000_000),
            ],
            1,
    ):
        track = Track(
            title=title,
            artist_list=[artist],
            year=2025,
            songstats_identifiers=SongstatsIdentifiers(
                songstats_id=f"id_{i}",
                songstats_title=title,
            ),
        )
        platform_stats = PlatformStats(
            spotify=SpotifyStats(streams_total=streams, popularity_peak=80 + i)
        )
        tracks.append(
            TrackWithStats(
                track=track,
                songstats_identifiers=track.songstats_identifiers,
                platform_stats=platform_stats,
            )
        )

    # Compute rankings
    scorer = PowerRankingScorer()
    results = scorer.compute_rankings(tracks)

    print(f"  Computed rankings for {results.total_tracks} tracks:")
    print()

    for ranking in results.rankings:
        print(
            f"    #{ranking.rank}: {ranking.track.title} - {ranking.artist_display} "
            f"(score: {ranking.total_score:.4f})"
        )

    print()
    print("  Top track details:")
    top = results.rankings[0]
    print(f"    Track: {top.track.title}")
    print(f"    Total Score: {top.total_score:.4f}")
    print(f"    Category Scores:")

    for cat_score in sorted(
            top.category_scores,
            key=lambda x: x.weighted_score,
            reverse=True,
    )[:3]:
        print(
            f"      • {cat_score.category}: {cat_score.weighted_score:.4f} (weight={cat_score.weight})"
        )


def demo_pipeline_data_flow() -> None:
    """Demonstrate data flow through pipeline stages."""
    print_separator("Pipeline Data Flow")

    print("Complete Pipeline Flow:")
    print()

    print("Stage 1: Extraction")
    print("- Input:  MusicBee library XML")
    print("- Process: Extract tracks → Search Songstats → Get IDs")
    print("- Output: list[Track] with Songstats IDs")
    print("- Storage: JSONTrackRepository\n")

    print("Stage 2: Enrichment")
    print("- Input:  list[Track] with Songstats IDs")
    print("- Process: Fetch stats → Fetch peaks → Fetch YouTube")
    print("- Output: list[TrackWithStats] with platform data")
    print("- Storage: JSONStatsRepository\n")

    print("Stage 3: Ranking")
    print("- Input:  list[TrackWithStats]")
    print("- Process: Compute rankings → Normalize → Weight → Sort")
    print("- Output: PowerRankingResults")
    print("- Storage: JSON (nested/flat), CSV\n")

    print("Key Features:")
    print("  • Each stage is independent (can run separately)")
    print("  • Checkpoint resumability (recover from failures)")
    print("  • Observer pattern (progress tracking, logging, metrics)")
    print("  • Repository pattern (clean data access)")
    print("  • Type-safe models (Pydantic validation)")


def demo_etl_pattern() -> None:
    """Demonstrate ETL pattern implementation."""
    print_separator("ETL Pattern (Extract-Transform-Load)")

    print("Each pipeline stage follows the ETL pattern:")
    print()

    print("PipelineStage[T, U] - Generic base class")
    print()

    print("  1. extract() -> T:")
    print("     Load input data (from repository, file, API)")
    print()

    print("  2. transform(data: T) -> U:")
    print("     Process and transform data")
    print("     (search, enrich, compute rankings)")
    print()

    print("  3. load(data: U) -> None:")
    print("     Save output data (to repository, file)")
    print()

    print("  4. run() -> U:")
    print("     Execute full ETL cycle")
    print("     - Calls extract() → transform() → load()")
    print("     - Returns transformed data")
    print()

    print("Example: ExtractionStage[list[dict], list[Track]]")
    print("  • extract() → Load MusicBee tracks (list[dict])")
    print("  • transform() → Search Songstats, create Track models (list[Track])")
    print("  • load() → Save to JSONTrackRepository")
    print()

    print("Benefits:")
    print("  ✓ Clear separation of concerns")
    print("  ✓ Testable in isolation (mock extract/load)")
    print("  ✓ Reusable pattern across all stages")
    print("  ✓ Type-safe with generics")


def main() -> None:
    """Run all pipeline stages demos."""
    print("=" * 80)
    print(" Pipeline Stages - Conceptual Demo")
    print("=" * 80)

    cleanup_demo_files()

    try:
        demo_extraction_stage_concept()
        demo_enrichment_stage_concept()
        demo_ranking_stage_concept()
        demo_pipeline_data_flow()
        demo_etl_pattern()

        print_separator()
        print("✓ All demos completed successfully!")
        print()
        print("Key Takeaways:")
        print("1. ExtractionStage: MusicBee → Songstats ID resolution")
        print("2. EnrichmentStage: Fetch comprehensive platform statistics")
        print("3. RankingStage: Compute power rankings + export")
        print("4. Each stage follows ETL pattern (Extract-Transform-Load)")
        print("5. Checkpoint resumability at each stage")
        print("6. Observer pattern for progress tracking")
        print("7. Repository pattern for data persistence")
        print()
        print("To run the full pipeline:")
        print("  See sandbox_orchestrator_demo.py (requires API credentials)")
        print()

    finally:
        cleanup_demo_files()
        print("✓ Demo files cleaned up")


if __name__ == "__main__":
    main()
