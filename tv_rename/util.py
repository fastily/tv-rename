"""Shared utility functions/classes for tv_rename"""

import logging
import pickle
import re

from getpass import getuser
from os import environ
from pathlib import Path
from typing import Any

from tvdb_v4_official import TVDB


VIDEO_EXTS = {".mkv", ".mp4", ".avi"}
_MY_TVDB: TVDB | None = None

log = logging.getLogger(__name__)


class Episode:
    """Simple representation of a TV episode"""

    def __init__(self, e: dict[str, Any]):
        """Initializer, creates a new `Episode` based on json from TheTVDB.

        Args:
            e (dict[str, Any]): The raw json from TheTVDB representing the episode to create.
        """
        self.id: int = e["id"]
        self.name: str = e["name"]
        self.episode_number: int = e["number"]
        self.absolute_number: int = e["absoluteNumber"]
        self.season_number: int = e["seasonNumber"]

        # self.sanitized_name = self.name.replace(":", "").replace("/", "_")
        self.local_path: Path | None = None

    def __repr__(self) -> str:
        """Creates a debug representation of this `Episode`

        Returns:
            str: The debug representation of this `Episode`
        """
        return f"{self.id} | {self.absolute_number:02} | s{self.season_number:02}e{self.episode_number:02} | {self.name}"


def episodes_of(tvdb: TVDB, series_id: int, season_type: str = "official") -> list[Episode]:
    """Lists episodes for the specified TheTVDB series id

    Args:
        tvdb (TVDB): The TVDB object to use
        series_id (int): TheTVDB series id to use
        season_type (str, optional): The season type.  Options are `"dvd"`, `"alternate"`, `"absolute"`, or `"official"`. Defaults to "official".

    Returns:
        list[Episode]: The episodes for the specified `series_id`, in the order of `season_type`.
    """
    return [Episode(e) for e in tvdb.get_series_episodes(series_id, season_type)["episodes"] if e["seasonNumber"]]  # page=0


def fetch_tvdb() -> TVDB:
    """Creates a `TVDB` object or loads a cached version from disk if applicable

    Raises:
        Exception: If `THETVDB_KEY` is not set as an environment variable

    Returns:
        TVDB: A `TVDB` object based on env var `THETVDB_KEY`
    """
    global _MY_TVDB

    if not _MY_TVDB:
        if (p := Path(f"/tmp/{getuser()}_tvdb.pickle")).is_file():
            log.debug("loading tvdb credentials from '%s'", p)

            with p.open("rb") as f:
                _MY_TVDB = pickle.load(f)
        else:
            if not (api_key := environ.get("THETVDB_KEY")):
                raise Exception("'THETVDB_KEY' env var is not set!")

            _MY_TVDB = TVDB(api_key)
            with p.open("wb") as f:
                pickle.dump(_MY_TVDB, f)

    return _MY_TVDB


def natural_sort(s: Path) -> list[int | str]:
    """Comparator function that generates a comparison key for `s`, implements natural sort.

    Args:
        s (Path): The `Path` being compared

    Returns:
        list[int | str]: the comparison key for `s`
    """
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', str(s))]
