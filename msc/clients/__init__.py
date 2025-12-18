"""External API clients."""

# Local
from msc.clients.base import BaseClient
from msc.clients.songstats import SongstatsClient
from msc.clients.youtube import YouTubeClient

__all__ = ["BaseClient", "SongstatsClient", "YouTubeClient"]
