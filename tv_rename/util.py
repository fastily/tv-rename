"""Shared utility functions/classes for tv_rename"""

import logging
import re
import pickle

from getpass import getuser
from os import environ
from pathlib import Path

from tvdb_v4_official import TVDB


VIDEO_EXTS = {".mkv", ".mp4", ".avi"}
_MY_TVDB: TVDB | None = None

log = logging.getLogger(__name__)


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
