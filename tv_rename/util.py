"""Shared utility functions/classes for tv_rename"""

import logging
import pickle
import re

from argparse import ArgumentParser
from getpass import getuser
from os import environ
from pathlib import Path
from typing import Any

from rich.logging import RichHandler
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


def configure_logging() -> None:
    """Configures settings logging with rich."""
    lg = logging.getLogger()
    lg.addHandler(RichHandler(rich_tracebacks=True))
    lg.setLevel(logging.DEBUG)


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


def find_all_eps(root_dir: Path, lex_sort: bool = True, ext: str = None) -> list[Path]:
    """Finds all episode files in a directory.  Assumes that `root_dir` contains directories of the format `Season *`.

    Args:
        root_dir (Path): The directory containing the Season directories.
        lex_sort (bool, optional): Set `True` to lexicographically (alphabetically) sort the output, otherwise natural ordering will be used. Defaults to `True`.
        ext (str, optional): Override default file extensions used to find tv episodes.  Useful for processing subtitle files.  Defaults to `None`.

    Returns:
        Path: The tv episodes found in `root_dir`
    """
    exts = {ext} if ext else VIDEO_EXTS
    return sorted([p for p in root_dir.glob("*/*") if p.is_file() and p.suffix.lower() in exts], key=None if lex_sort else natural_sort)


def natural_sort(s: Path) -> list[int | str]:
    """Comparator function that generates a comparison key for `s`, implements natural sort.

    Args:
        s (Path): The `Path` being compared

    Returns:
        list[int | str]: the comparison key for `s`
    """
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', str(s))]


def resolve_alt_type(absolute: bool, streaming: bool) -> str:
    """Used to check CLI input to see if user specified the source episodes as absolute, streaming, or dvd.  Returns a `str` identifier representing the user's choice.

    Args:
        absolute (bool): The argparse flag associated with `--absolute`
        streaming (bool): The argparse flag associated with `--streaming`.

    Returns:
        str: The identifier associated with the user-specified source
    """
    if absolute:
        return "absolute"
    elif streaming:
        return "streaming"

    return "dvd"


def shared_abs_stream_opts() -> ArgumentParser:
    """Creates an `ArgumentParser` with shared options for modules that require the user to specify if the source should be treated as `absolute`, `streaming`, or `dvd` ordering.  Useful for passing in via the `parents` param for child `ArgumentParser` objects

    Returns:
        ArgumentParser: The `ArgumentParser` that contains shared options specifying if the source should be treated as `absolute`, `streaming`, or `dvd` ordering.
    """
    p = ArgumentParser(add_help=False)
    p.add_argument('--absolute', action='store_true', help="Treat input as absolute ordering")
    p.add_argument('--streaming', action='store_true', help="Treat input dirs as streaming ordering")
    return p


def shared_cli_opts() -> ArgumentParser:
    """Creates an `ArgumentParser` with shared options across all `tv_rename` modules.  Useful for passing in via the `parents` param for child `ArgumentParser` objects

    Returns:
        ArgumentParser: The `ArgumentParser` that contains shared options for all `tv_rename` modules
    """
    p = ArgumentParser(add_help=False)
    p.add_argument('-l', action='store_true', help="Use lexigraphical sort instead of natural sort")
    p.add_argument('-s', action='store_true', help="Dry run, don't actually rename any files/dirs")
    p.add_argument('-x', type=str, metavar="ext", help=f"The file extensions to target.  Defaults to {', '.join(VIDEO_EXTS)}")
    return p


def shared_series_id_root_dir() -> ArgumentParser:
    """Creates an `ArgumentParser` which allows a user to specify a TheTVDB `series_id` and a `root_dir` for a series.  Useful for passing in via the `parents` param for child `ArgumentParser` objects

    Returns:
        ArgumentParser: The `ArgumentParser` that allows a user to specify a TheTVDB `series_id` and a `root_dir` for a series
    """
    p = ArgumentParser(add_help=False)
    p.add_argument('series_id', type=int, help='The series id of the show in question on thetvdb')
    p.add_argument('root_dir', type=Path, nargs='?', default=Path("."), help='the series directory to work on.  Defaults to the current working directory')
    return p
