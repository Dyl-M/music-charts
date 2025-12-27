"""Fixtures for clients module tests."""

# Standard library
from pathlib import Path
from unittest.mock import MagicMock, patch

# Third-party
import pytest


@pytest.fixture
def mock_session():
    """Create a mock requests session."""
    with patch("requests.Session") as mock:
        session = MagicMock()
        mock.return_value = session
        yield session


@pytest.fixture
def temp_library_file(tmp_path: Path) -> Path:
    """Create a temporary MusicBee library XML file."""
    library_xml = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" "https://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Major Version</key><integer>1</integer>
    <key>Minor Version</key><integer>1</integer>
    <key>Application Version</key><string>3.5.8447</string>
    <key>Music Folder</key><string>file://localhost/E:/Musique/</string>
    <key>Library Persistent ID</key><string>E96F1D18F0C9D00B</string>
    <key>Tracks</key>
    <dict>
        <key>123</key>
        <dict>
            <key>Track ID</key><integer>123</integer>
            <key>Name</key><string>Test Track</string>
            <key>Artist</key><string>Test Artist</string>
            <key>Year</key><integer>2024</integer>
        </dict>
    </dict>
    <key>Playlists</key>
    <array>
        <dict>
            <key>Name</key><string>Test Playlist</string>
            <key>Playlist ID</key><integer>4361</integer>
            <key>Playlist Persistent ID</key><string>ABCDEF123456</string>
            <key>Playlist Items</key>
            <array>
                <dict>
                    <key>Track ID</key><integer>123</integer>
                </dict>
            </array>
        </dict>
    </array>
</dict>
</plist>"""
    library_file = tmp_path / "library.xml"
    library_file.write_text(library_xml, encoding="utf-8")
    return library_file


@pytest.fixture
def mock_songstats_response():
    """Create a mock Songstats API response."""
    return {
        "results": [
            {
                "songstats_track_id": "abc123",
                "title": "Test Track",
                "artists": [{"name": "Test Artist"}],
                "isrc": "USRC12345678",
            }
        ]
    }


@pytest.fixture
def mock_songstats_stats_response():
    """Create a mock Songstats stats API response."""
    return {
        "stats": [
            {
                "source": "spotify",
                "data": {
                    "streams_total": 1000000,
                    "popularity_peak": 75,
                }
            },
            {
                "source": "deezer",
                "data": {
                    "popularity_peak": 80,
                }
            }
        ]
    }


@pytest.fixture
def mock_youtube_video():
    """Create a mock YouTube video object."""
    video = MagicMock()
    video.id = "dQw4w9WgXcQ"
    video.snippet.title = "Test Video"
    video.snippet.description = "Test Description"
    video.snippet.channelId = "UC123"
    video.snippet.channelTitle = "Test Channel"
    video.snippet.publishedAt = "2020-01-01T00:00:00Z"
    video.contentDetails.duration = "PT3M30S"
    video.statistics.viewCount = "1000000"
    video.statistics.likeCount = "50000"
    video.statistics.commentCount = "1000"
    return video
