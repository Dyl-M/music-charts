"""Interactive demo for power ranking models.

This script demonstrates the CategoryScore, PowerRanking, and PowerRankingResults
models, including score calculations, filtering, and ranking analysis.

Requirements:
    - No external dependencies or setup required
    - Uses synthetic examples to demonstrate power ranking system

Usage:
    python _demos/sandbox_ranking_models_demo.py
"""

# Third-party
from pydantic import ValidationError

# Local
from msc.models.ranking import CategoryScore, PowerRanking, PowerRankingResults
from msc.models.track import Track


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


def demo_category_score_creation() -> None:
    """Demonstrate CategoryScore creation and validation."""
    print_separator("CategoryScore Creation and Validation")

    # Valid score with different weight levels
    print("Creating CategoryScore with different weight levels...")

    # High weight (×4) for streams
    streams_score = CategoryScore(
        category="streams",
        raw_score=0.85,
        weight=4,
        weighted_score=3.4
    )
    print(f"✓ Streams (high weight=4):")
    print(f"    raw_score: {streams_score.raw_score}")
    print(f"    weight: {streams_score.weight}")
    print(f"    weighted_score: {streams_score.weighted_score}")
    print(f"    (0.85 × 4 = 3.4)\n")

    # Low weight (×2) for playlists
    playlists_score = CategoryScore(
        category="playlists",
        raw_score=0.60,
        weight=2,
        weighted_score=1.2
    )
    print(f"  Playlists (low weight=2):")
    print(f"    weighted_score: {playlists_score.weighted_score}")
    print(f"    (0.60 × 2 = 1.2)\n")

    # Negligible weight (×1) for charts
    charts_score = CategoryScore(
        category="charts",
        raw_score=0.40,
        weight=1,
        weighted_score=0.4
    )
    print(f"  Charts (negligible weight=1):")
    print(f"    weighted_score: {charts_score.weighted_score}")
    print(f"    (0.40 × 1 = 0.4)\n")

    # Validation: raw_score must be 0.0-1.0
    print("Testing raw_score validation (must be 0.0-1.0)...")
    try:
        CategoryScore(category="test", raw_score=1.5, weight=2, weighted_score=3.0)
    except ValidationError:
        print("✗ raw_score=1.5 rejected (exceeds 1.0)")

    try:
        CategoryScore(category="test", raw_score=-0.1, weight=2, weighted_score=-0.2)
    except ValidationError:
        print("✗ raw_score=-0.1 rejected (below 0.0)\n")

    # Validation: weight must be 1-4
    print("Testing weight validation (must be 1-4)...")
    try:
        CategoryScore(category="test", raw_score=0.5, weight=5, weighted_score=2.5)
    except ValidationError:
        print("✗ weight=5 rejected (exceeds 4)")

    try:
        CategoryScore(category="test", raw_score=0.5, weight=0, weighted_score=0.0)
    except ValidationError:
        print("✗ weight=0 rejected (below 1)\n")

    print("✓ CategoryScore creation and validation working correctly\n")


def demo_power_ranking_creation() -> None:
    """Demonstrate PowerRanking creation and properties."""
    print_separator("PowerRanking Creation and Properties")

    # Single artist track
    print("Creating PowerRanking for single artist track...")
    track1 = Track(
        title="Scary Monsters and Nice Sprites",
        artist_list=["skrillex"],
        year=2010
    )
    scores1 = [
        CategoryScore(category="streams", raw_score=0.95, weight=4, weighted_score=3.8),
        CategoryScore(category="popularity", raw_score=0.90, weight=4, weighted_score=3.6),
        CategoryScore(category="playlists", raw_score=0.75, weight=2, weighted_score=1.5),
    ]
    ranking1 = PowerRanking(
        track=track1,
        total_score=8.9,
        rank=1,
        category_scores=scores1
    )

    print(f"✓ Rank #{ranking1.rank}: {ranking1.track.title}")
    print(f"  Artist display: {ranking1.artist_display}")
    print(f"  Total score: {ranking1.total_score}")
    print(f"  Category breakdown:")
    for score in ranking1.category_scores:
        print(f"    {score.category}: {score.weighted_score} (raw={score.raw_score}, weight={score.weight})")
    print()

    # Multiple artist collaboration
    print("Creating PowerRanking for collaboration track...")
    track2 = Track(
        title="16",
        artist_list=["blasterjaxx", "hardwell", "maddix"],
        year=2024
    )
    scores2 = [
        CategoryScore(category="streams", raw_score=0.85, weight=4, weighted_score=3.4),
        CategoryScore(category="popularity", raw_score=0.80, weight=4, weighted_score=3.2),
    ]
    ranking2 = PowerRanking(
        track=track2,
        total_score=6.6,
        rank=2,
        category_scores=scores2
    )

    print(f"✓ Rank #{ranking2.rank}: {ranking2.track.title}")
    print(f"  Artist display: {ranking2.artist_display}")
    print(f"  (Multiple artists joined with ' & ')\\n")

    # Validation: total_score must be >= 0
    print("Testing validation (total_score must be >= 0)...")
    try:
        PowerRanking(
            track=track1,
            total_score=-5.0,
            rank=1,
            category_scores=scores1
        )
    except ValidationError:
        print("✗ total_score=-5.0 rejected (must be >= 0)\n")

    # Validation: category_scores must have at least 1 score
    print("Testing validation (category_scores min_length=1)...")
    try:
        PowerRanking(
            track=track1,
            total_score=5.0,
            rank=1,
            category_scores=[]
        )
    except ValidationError:
        print("✗ category_scores=[] rejected (must have at least 1 score)\n")

    print("✓ PowerRanking creation and properties working correctly\n")


def demo_power_ranking_results() -> None:
    """Demonstrate PowerRankingResults collection and methods."""
    print_separator("PowerRankingResults Collection and Methods")

    # Create sample rankings
    print("Creating sample PowerRankingResults with 5 tracks...")

    tracks_data = [
        ("Animals", ["martin garrix"], 2013, 15.7),
        ("Titanium", ["david guetta", "sia"], 2011, 14.2),
        ("16", ["blasterjaxx", "hardwell", "maddix"], 2024, 12.8),
        ("Levels", ["avicii"], 2011, 11.5),
        ("Spaceman", ["hardwell"], 2012, 10.3),
    ]

    rankings = []
    for idx, (title, artists, year, score) in enumerate(tracks_data, 1):
        track = Track(title=title, artist_list=artists, year=year)
        category_scores = [
            CategoryScore(category="streams", raw_score=0.8, weight=4, weighted_score=3.2)
        ]
        ranking = PowerRanking(
            track=track,
            total_score=score,
            rank=idx,
            category_scores=category_scores
        )
        rankings.append(ranking)

    results = PowerRankingResults(rankings=rankings, year=2024)

    print(f"✓ Created PowerRankingResults:")
    print(f"  Year: {results.year}")
    print(f"  Total tracks: {results.total_tracks}\n")

    # Display rankings
    print("  Rankings:")
    for ranking in results.rankings[:5]:
        print(f"    #{ranking.rank}: {ranking.track.title} by {ranking.artist_display} ({ranking.total_score})")
    print()

    # get_by_rank method
    print("Testing get_by_rank() method...")
    top_track = results.get_by_rank(1)
    if top_track:
        print(f"✓ Rank #1: {top_track.track.title} ({top_track.total_score})")
    not_found = results.get_by_rank(99)
    print(f"  Rank #99: {not_found} (not found)\n")

    # get_by_artist method (case-insensitive)
    print("Testing get_by_artist() method (case-insensitive)...")
    hardwell_tracks = results.get_by_artist("hardwell")
    print(f"✓ Tracks featuring 'hardwell': {len(hardwell_tracks)} found")
    for ranking in hardwell_tracks:
        print(f"    #{ranking.rank}: {ranking.track.title} by {ranking.artist_display}")
    print()

    # Case-insensitive search
    print("Testing case-insensitive artist search...")
    print(f"  'hardwell': {len(results.get_by_artist('hardwell'))} tracks")
    print(f"  'HARDWELL': {len(results.get_by_artist('HARDWELL'))} tracks")
    print(f"  'Hardwell': {len(results.get_by_artist('Hardwell'))} tracks")
    print(f"  (All return the same results)\n")

    # Validation: rankings must have at least 1 ranking
    print("Testing validation (rankings min_length=1)...")
    try:
        PowerRankingResults(rankings=[], year=2024)
    except ValidationError:
        print("✗ rankings=[] rejected (must have at least 1 ranking)\n")

    print("✓ PowerRankingResults methods working correctly\n")


def demo_complete_ranking_example() -> None:
    """Demonstrate complete power ranking workflow."""
    print_separator("Complete Power Ranking Example")

    print("Building a complete power ranking for 2024 hard techno tracks...\n")

    # Define tracks with realistic scores
    tracks_info = [
        {
            "title": "16",
            "artists": ["blasterjaxx", "hardwell", "maddix"],
            "categories": [
                ("streams", 0.85, 4),
                ("popularity", 0.82, 4),
                ("playlists", 0.70, 2),
                ("charts", 0.50, 1),
            ]
        },
        {
            "title": "Acid",
            "artists": ["reinier zonneveld", "omar"],
            "categories": [
                ("streams", 0.78, 4),
                ("popularity", 0.75, 4),
                ("playlists", 0.65, 2),
                ("charts", 0.45, 1),
            ]
        },
        {
            "title": "Rave",
            "artists": ["maddix"],
            "categories": [
                ("streams", 0.72, 4),
                ("popularity", 0.70, 4),
                ("playlists", 0.60, 2),
                ("charts", 0.40, 1),
            ]
        },
    ]

    # Build track data and calculate total scores
    track_data = []
    for info in tracks_info:
        track = Track(
            title=info["title"],
            artist_list=info["artists"],
            year=2024
        )

        # Calculate scores
        category_scores = []
        total = 0.0
        for cat_name, raw, weight in info["categories"]:
            weighted = raw * weight
            total += weighted
            category_scores.append(
                CategoryScore(
                    category=cat_name,
                    raw_score=raw,
                    weight=weight,
                    weighted_score=weighted
                )
            )

        track_data.append({
            "track": track,
            "total_score": round(total, 2),
            "category_scores": category_scores
        })

    # Sort by total_score and create rankings with correct ranks
    track_data.sort(key=lambda t: t["total_score"], reverse=True)
    rankings_with_rank = []
    for idx, data in enumerate(track_data, 1):
        rankings_with_rank.append(
            PowerRanking(
                track=data["track"],
                total_score=data["total_score"],
                rank=idx,
                category_scores=data["category_scores"]
            )
        )

    # Create results
    results = PowerRankingResults(rankings=rankings_with_rank, year=2024)

    # Display results
    print(f"2024 Hard Techno Power Rankings")
    print(f"{'='*60}\n")

    for ranking in results.rankings:
        print(f"Rank #{ranking.rank}: {ranking.track.title}")
        print(f"  Artist(s): {ranking.artist_display}")
        print(f"  Total Score: {ranking.total_score}")
        print(f"  Score Breakdown:")
        for score in ranking.category_scores:
            print(f"    - {score.category.capitalize()}: "
                  f"{score.weighted_score:.2f} "
                  f"(raw={score.raw_score:.2f} × weight={score.weight})")
        print()

    # Analysis
    print(f"Analysis:")
    print(f"  Total tracks ranked: {results.total_tracks}")
    print(f"  Top ranked track: {results.get_by_rank(1).track.title if results.get_by_rank(1) else 'N/A'}")
    print(f"  Maddix appearances: {len(results.get_by_artist('maddix'))} tracks\n")

    print("✓ Complete ranking example working correctly\n")


def demo_json_serialization() -> None:
    """Demonstrate JSON serialization of rankings."""
    print_separator("JSON Serialization")

    # Create simple ranking
    track = Track(title="Test", artist_list=["artist"], year=2024)
    category_scores = [
        CategoryScore(category="streams", raw_score=0.8, weight=4, weighted_score=3.2)
    ]
    ranking = PowerRanking(
        track=track,
        total_score=3.2,
        rank=1,
        category_scores=category_scores
    )

    # Serialize
    print("Serializing PowerRanking to JSON...")
    json_str = ranking.model_dump_json(indent=2)
    print(json_str[:300] + "...\n")

    # Deserialize
    print("Deserializing from JSON...")
    loaded_ranking = PowerRanking.model_validate_json(json_str)
    print(f"✓ Loaded: {loaded_ranking.track.title} (rank #{loaded_ranking.rank})\n")

    print("✓ JSON serialization working correctly\n")


def demo_immutability() -> None:
    """Demonstrate model immutability."""
    print_separator("Model Immutability")

    track = Track(title="Test", artist_list=["artist"], year=2024)
    category_scores = [
        CategoryScore(category="test", raw_score=0.5, weight=1, weighted_score=0.5)
    ]
    ranking = PowerRanking(
        track=track,
        total_score=5.0,
        rank=1,
        category_scores=category_scores
    )

    print("Attempting to modify frozen PowerRanking...")
    try:
        ranking.rank = 2
        print("✗ Modification succeeded (unexpected)")
    except ValidationError:
        print("✓ Modification rejected (model is frozen)")

    print("  Reason: ConfigDict(frozen=True) makes models immutable")
    print("  Benefits: Data integrity, thread safety, hashability\n")

    print("✓ Immutability working as expected\n")


def main() -> None:
    """Run all power ranking model demos."""
    print("=" * 80)
    print(" Power Ranking Models - Interactive Demo")
    print("=" * 80)

    demo_category_score_creation()
    demo_power_ranking_creation()
    demo_power_ranking_results()
    demo_complete_ranking_example()
    demo_json_serialization()
    demo_immutability()

    print_separator()
    print("✓ All demos completed successfully!")
    print()


if __name__ == "__main__":
    main()
