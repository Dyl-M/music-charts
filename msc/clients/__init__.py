"""External API clients."""

# Local
from msc.clients.base import BaseClient
from msc.clients.songstats import SongstatsClient

__all__ = ["BaseClient", "SongstatsClient"]
