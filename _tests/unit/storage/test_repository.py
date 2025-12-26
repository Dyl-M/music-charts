"""Unit tests for repository interfaces.

Tests abstract Repository, TrackRepository, and StatsRepository interfaces.
"""
from abc import ABC

# Third-party
import pytest

# Local
from msc.storage.repository import Repository, TrackRepository, StatsRepository
from msc.models.track import Track
from msc.models.stats import TrackWithStats


class TestRepositoryInterface:
    """Tests for abstract Repository interface."""

    @staticmethod
    def test_cannot_instantiate_directly() -> None:
        """Should not allow direct instantiation."""
        with pytest.raises(TypeError, match="abstract"):
            # noinspection PyAbstractClass
            Repository()

    @staticmethod
    def test_add_is_abstract() -> None:
        """Should require add method implementation."""

        class IncompleteRepo(Repository, ABC):
            """Repository missing add method."""

            def get(self, identifier: str):
                return None

            def get_all(self):
                return []

            def exists(self, identifier: str):
                return False

            def remove(self, identifier: str):
                raise NotImplementedError()

            def clear(self):
                raise NotImplementedError()

            def count(self):
                return 0

        with pytest.raises(TypeError, match="add"):
            # noinspection PyAbstractClass
            IncompleteRepo()

    @staticmethod
    def test_get_is_abstract() -> None:
        """Should require get method implementation."""

        class IncompleteRepo(Repository, ABC):
            """Repository missing get method."""

            def add(self, item):
                raise NotImplementedError()

            def get_all(self):
                return []

            def exists(self, identifier: str):
                return False

            def remove(self, identifier: str):
                raise NotImplementedError()

            def clear(self):
                raise NotImplementedError()

            def count(self):
                return 0

        with pytest.raises(TypeError, match="get"):
            # noinspection PyAbstractClass
            IncompleteRepo()

    @staticmethod
    def test_get_all_is_abstract() -> None:
        """Should require get_all method implementation."""

        class IncompleteRepo(Repository, ABC):
            """Repository missing get_all method."""

            def add(self, item):
                raise NotImplementedError()

            def get(self, identifier: str):
                return None

            def exists(self, identifier: str):
                return False

            def remove(self, identifier: str):
                raise NotImplementedError()

            def clear(self):
                raise NotImplementedError()

            def count(self):
                return 0

        with pytest.raises(TypeError, match="get_all"):
            # noinspection PyAbstractClass
            IncompleteRepo()

    @staticmethod
    def test_exists_is_abstract() -> None:
        """Should require exists method implementation."""

        class IncompleteRepo(Repository, ABC):
            """Repository missing exists method."""

            def add(self, item):
                raise NotImplementedError()

            def get(self, identifier: str):
                return None

            def get_all(self):
                return []

            def remove(self, identifier: str):
                raise NotImplementedError()

            def clear(self):
                raise NotImplementedError()

            def count(self):
                return 0

        with pytest.raises(TypeError, match="exists"):
            # noinspection PyAbstractClass
            IncompleteRepo()

    @staticmethod
    def test_remove_is_abstract() -> None:
        """Should require remove method implementation."""

        class IncompleteRepo(Repository, ABC):
            """Repository missing remove method."""

            def add(self, item):
                raise NotImplementedError()

            def get(self, identifier: str):
                return None

            def get_all(self):
                return []

            def exists(self, identifier: str):
                return False

            def clear(self):
                raise NotImplementedError()

            def count(self):
                return 0

        with pytest.raises(TypeError, match="remove"):
            # noinspection PyAbstractClass
            IncompleteRepo()

    @staticmethod
    def test_clear_is_abstract() -> None:
        """Should require clear method implementation."""

        class IncompleteRepo(Repository, ABC):
            """Repository missing clear method."""

            def add(self, item):
                raise NotImplementedError()

            def get(self, identifier: str):
                return None

            def get_all(self):
                return []

            def exists(self, identifier: str):
                return False

            def remove(self, identifier: str):
                raise NotImplementedError()

            def count(self):
                return 0

        with pytest.raises(TypeError, match="clear"):
            # noinspection PyAbstractClass
            IncompleteRepo()

    @staticmethod
    def test_count_is_abstract() -> None:
        """Should require count method implementation."""

        class IncompleteRepo(Repository, ABC):
            """Repository missing count method."""

            def add(self, item):
                raise NotImplementedError()

            def get(self, identifier: str):
                return None

            def get_all(self):
                return []

            def exists(self, identifier: str):
                return False

            def remove(self, identifier: str):
                raise NotImplementedError()

            def clear(self):
                raise NotImplementedError()

        with pytest.raises(TypeError, match="count"):
            # noinspection PyAbstractClass
            IncompleteRepo()


class TestTrackRepositoryInterface:
    """Tests for abstract TrackRepository interface."""

    @staticmethod
    def test_cannot_instantiate_directly() -> None:
        """Should not allow direct instantiation."""
        with pytest.raises(TypeError, match="abstract"):
            # noinspection PyAbstractClass
            TrackRepository()

    @staticmethod
    def test_find_by_title_artist_is_abstract() -> None:
        """Should require find_by_title_artist method implementation."""

        class IncompleteRepo(TrackRepository, ABC):
            """Repository missing find_by_title_artist method."""

            def add(self, item: Track):
                raise NotImplementedError()

            def get(self, identifier: str):  # skipcq: PYL-R0201
                return None

            def get_all(self):  # skipcq: PYL-R0201
                return []

            def exists(self, identifier: str):  # skipcq: PYL-R0201
                return False

            def remove(self, identifier: str):
                raise NotImplementedError()

            def clear(self):
                raise NotImplementedError()

            def count(self):  # skipcq: PYL-R0201
                return 0

            def get_unprocessed(self, processed_ids: set[str]):  # skipcq: PYL-R0201
                return []

        with pytest.raises(TypeError, match="find_by_title_artist"):
            # noinspection PyAbstractClass
            IncompleteRepo()

    @staticmethod
    def test_get_unprocessed_is_abstract() -> None:
        """Should require get_unprocessed method implementation."""

        class IncompleteRepo(TrackRepository, ABC):
            """Repository missing get_unprocessed method."""

            def add(self, item: Track):
                raise NotImplementedError()

            def get(self, identifier: str):  # skipcq: PYL-R0201
                return None

            def get_all(self):  # skipcq: PYL-R0201
                return []

            def exists(self, identifier: str):  # skipcq: PYL-R0201
                return False

            def remove(self, identifier: str):
                raise NotImplementedError()

            def clear(self):
                raise NotImplementedError()

            def count(self):  # skipcq: PYL-R0201
                return 0

            def find_by_title_artist(self, title: str, artist: str):  # skipcq: PYL-R0201
                return None

        with pytest.raises(TypeError, match="get_unprocessed"):
            # noinspection PyAbstractClass
            IncompleteRepo()


class TestStatsRepositoryInterface:
    """Tests for abstract StatsRepository interface."""

    @staticmethod
    def test_cannot_instantiate_directly() -> None:
        """Should not allow direct instantiation."""
        with pytest.raises(TypeError, match="abstract"):
            # noinspection PyAbstractClass
            StatsRepository()

    @staticmethod
    def test_save_batch_is_abstract() -> None:
        """Should require save_batch method implementation."""

        class IncompleteRepo(StatsRepository, ABC):
            """Repository missing save_batch method."""

            def add(self, item: TrackWithStats):
                raise NotImplementedError()

            def get(self, identifier: str):  # skipcq: PYL-R0201
                return None

            def get_all(self):  # skipcq: PYL-R0201
                return []

            def exists(self, identifier: str):  # skipcq: PYL-R0201
                return False

            def remove(self, identifier: str):
                raise NotImplementedError()

            def clear(self):
                raise NotImplementedError()

            def count(self):  # skipcq: PYL-R0201
                return 0

            def export_to_json(self, file_path, flat=False):
                raise NotImplementedError()

            def export_to_csv(self, file_path):
                raise NotImplementedError()

            def get_by_songstats_id(self, songstats_id: str):  # skipcq: PYL-R0201
                return None

        with pytest.raises(TypeError, match="save_batch"):
            # noinspection PyAbstractClass
            IncompleteRepo()

    @staticmethod
    def test_export_to_json_is_abstract() -> None:
        """Should require export_to_json method implementation."""

        class IncompleteRepo(StatsRepository, ABC):
            """Repository missing export_to_json method."""

            def add(self, item: TrackWithStats):
                raise NotImplementedError()

            def get(self, identifier: str):  # skipcq: PYL-R0201
                return None

            def get_all(self):  # skipcq: PYL-R0201
                return []

            def exists(self, identifier: str):  # skipcq: PYL-R0201
                return False

            def remove(self, identifier: str):
                raise NotImplementedError()

            def clear(self):
                raise NotImplementedError()

            def count(self):  # skipcq: PYL-R0201
                return 0

            def save_batch(self, items):
                raise NotImplementedError()

            def export_to_csv(self, file_path):
                raise NotImplementedError()

            def get_by_songstats_id(self, songstats_id: str):  # skipcq: PYL-R0201
                return None

        with pytest.raises(TypeError, match="export_to_json"):
            # noinspection PyAbstractClass
            IncompleteRepo()

    @staticmethod
    def test_export_to_csv_is_abstract() -> None:
        """Should require export_to_csv method implementation."""

        class IncompleteRepo(StatsRepository, ABC):
            """Repository missing export_to_csv method."""

            def add(self, item: TrackWithStats):
                raise NotImplementedError()

            def get(self, identifier: str):  # skipcq: PYL-R0201
                return None

            def get_all(self):  # skipcq: PYL-R0201
                return []

            def exists(self, identifier: str):  # skipcq: PYL-R0201
                return False

            def remove(self, identifier: str):
                raise NotImplementedError()

            def clear(self):
                raise NotImplementedError()

            def count(self):  # skipcq: PYL-R0201
                return 0

            def save_batch(self, items):
                raise NotImplementedError()

            def export_to_json(self, file_path, flat=False):
                raise NotImplementedError()

            def get_by_songstats_id(self, songstats_id: str):  # skipcq: PYL-R0201
                return None

        with pytest.raises(TypeError, match="export_to_csv"):
            # noinspection PyAbstractClass
            IncompleteRepo()

    @staticmethod
    def test_get_by_songstats_id_is_abstract() -> None:
        """Should require get_by_songstats_id method implementation."""

        class IncompleteRepo(StatsRepository, ABC):
            """Repository missing get_by_songstats_id method."""

            def add(self, item: TrackWithStats):
                raise NotImplementedError()

            def get(self, identifier: str):  # skipcq: PYL-R0201
                return None

            def get_all(self):  # skipcq: PYL-R0201
                return []

            def exists(self, identifier: str):  # skipcq: PYL-R0201
                return False

            def remove(self, identifier: str):
                raise NotImplementedError()

            def clear(self):
                raise NotImplementedError()

            def count(self):  # skipcq: PYL-R0201
                return 0

            def save_batch(self, items):
                raise NotImplementedError()

            def export_to_json(self, file_path, flat=False):
                raise NotImplementedError()

            def export_to_csv(self, file_path):
                raise NotImplementedError()

        with pytest.raises(TypeError, match="get_by_songstats_id"):
            # noinspection PyAbstractClass
            IncompleteRepo()
