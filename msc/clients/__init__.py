"""External API clients."""

# Local
from msc.clients.base import BaseClient
from msc.clients.musicbee import MusicBeeClient
from msc.clients.songstats import SongstatsClient
from msc.clients.youtube import YouTubeClient

__all__ = ["BaseClient", "MusicBeeClient", "SongstatsClient", "YouTubeClient"]
