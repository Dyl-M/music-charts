# Local
from msc.config.constants import TITLE_PATTERNS_TO_REMOVE, TITLE_PATTERNS_TO_SPACE

"""Text processing utilities for track titles and artist names."""


def format_title(track_title: str) -> str:
    """Format track title for API search queries.

    Removes common mix/remix suffixes and special characters that
    interfere with search accuracy.

    Args:
        track_title: Original track title from library.

    Returns:
        Cleaned and lowercase title suitable for API queries.

    Example:
        >>> format_title("Song Name [Extended Mix]")
        'song name'
        >>> format_title("Artist A × Artist B - Track")
        'artist a artist b - track'
    """
    result = track_title

    for pattern in TITLE_PATTERNS_TO_REMOVE:
        result = result.replace(pattern, "")

    for pattern in TITLE_PATTERNS_TO_SPACE:
        result = result.replace(pattern, " ")

    return result.strip().lower()


def remove_remixer(track_title: str, artist_list: list[str]) -> list[str]:
    """Remove remixer from artist list based on track title.

    If an artist name appears in the track title (typically as a remixer),
    they are excluded from the primary artist list.

    Args:
        track_title: Track title that may contain remixer name.
        artist_list: List of all credited artists.

    Returns:
        Filtered artist list with remixers removed.

    Example:
        >>> remove_remixer("original song (artist b remix)", ["artist a", "artist b"])
        ['artist a']
    """
    title_lower = track_title.lower()
    return [artist for artist in artist_list if artist.lower() not in title_lower]


def build_search_query(title: str, artists: list[str]) -> str:
    """Build a search query string from title and artists.

    Args:
        title: Formatted track title.
        artists: List of primary artists (remixers already filtered).

    Returns:
        Search query string for Songstats API.

    Example:
        >>> build_search_query("song name", ["artist a", "artist b"])
        'artist a, artist b song name'
    """
    artists_str = ", ".join(artists)
    return f"{artists_str} {title}".strip()


def normalize_label(label: str) -> str:
    """Normalize record label name for consistency.

    Args:
        label: Record label name.

    Returns:
        Lowercase, stripped label name.
    """
    return label.strip().lower()


def normalize_genre(genre: str) -> str:
    """Normalize genre name for consistency.

    Args:
        genre: Genre name.

    Returns:
        Lowercase, stripped genre name.
    """
    return genre.strip().lower()


def truncate(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """Truncate text to maximum length with suffix.

    Args:
        text: Text to truncate.
        max_length: Maximum length including suffix.
        suffix: Suffix to add when truncating.

    Returns:
        Truncated text or original if within limit.
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix
