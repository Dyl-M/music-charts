"""Text processing utilities for track titles and artist names."""

# Standard library
import re

# Local
from msc.config.constants import TITLE_PATTERNS_TO_REMOVE, TITLE_PATTERNS_TO_SPACE


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

    # Remove patterns case-insensitively (title may already be lowercased)
    for pattern in TITLE_PATTERNS_TO_REMOVE:
        # Use regex with IGNORECASE flag for case-insensitive replacement
        result = re.sub(re.escape(pattern), "", result, flags=re.IGNORECASE)

    for pattern in TITLE_PATTERNS_TO_SPACE:
        # Use regex with IGNORECASE flag for case-insensitive replacement
        result = re.sub(re.escape(pattern), " ", result, flags=re.IGNORECASE)

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


def format_artist(artist_name: str) -> str:
    """Format artist name for API search queries.

    Removes feature annotations, special characters, and extra punctuation
    that interfere with search accuracy. Featured artists are intentionally
    removed as they typically don't appear in Songstats main artist fields.

    Args:
        artist_name: Original artist name from library.

    Returns:
        Cleaned and lowercase artist name suitable for API queries.

    Example:
        >>> format_artist("Artist A (feat. Artist B)")
        'artist a'
        >>> format_artist("Artist A × Artist B")
        'artist a artist b'
        >>> format_artist("Artist A & Artist B")
        'artist a artist b'
    """
    result = artist_name

    # Remove feature annotations entirely (case-insensitive)
    # Match patterns like: (feat. ...), (ft. ...), (featuring ...), [feat. ...]
    # Remove them completely as they create query mismatches in Songstats
    result = re.sub(r'\s*[(\[](f(?:ea)?t\.?|featuring)\s+[^)\]]+[)\]]', '', result, flags=re.IGNORECASE)

    # Replace special separators with spaces
    result = result.replace('×', ' ')
    result = result.replace('&', ' ')

    # Remove remaining parentheses and brackets
    result = result.replace('(', '').replace(')', '')
    result = result.replace('[', '').replace(']', '')

    # Normalize whitespace and lowercase
    result = ' '.join(result.split())
    return result.strip().lower()


def build_search_query(title: str, artists: list[str]) -> str:
    """Build a search query string from title and artists.

    Args:
        title: Formatted track title.
        artists: List of primary artists (remixers already filtered).

    Returns:
        Search query string for Songstats API.

    Example:
        >>> build_search_query("song name", ["artist a", "artist b"])
        'artist a artist b song name'
    """
    # Clean artist names
    cleaned_artists = [format_artist(artist) for artist in artists]
    # Use space separator instead of comma to avoid punctuation in queries
    artists_str = " ".join(cleaned_artists)
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
