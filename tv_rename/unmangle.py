"""Program that renames dvd/streaming/absolute ordered episodes to aired ordering based using data from TheTVDB"""

import logging

from argparse import ArgumentParser
from collections.abc import Iterable
from typing import Any
from pathlib import Path

from rich.logging import RichHandler
from tvdb_v4_official import TVDB

from .util import fetch_tvdb, natural_sort, VIDEO_EXTS


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


def _episodes_of(tvdb: TVDB, series_id: int, season_type: str = "official") -> list[Episode]:
    """Lists episodes for the specified TheTVDB series id

    Args:
        tvdb (TVDB): The TVDB object to use
        series_id (int): TheTVDB series id to use
        season_type (str, optional): The season type.  Options are `"dvd"`, `"alternate"`, `"absolute"`, or `"official"`. Defaults to "official".

    Returns:
        list[Episode]: The episodes for the specified `series_id`, in the order of `season_type`.
    """
    return [Episode(e) for e in tvdb.get_series_episodes(series_id, season_type)["episodes"] if e["seasonNumber"]]  # page=0


def _counts_match(a: Iterable, b: Iterable, label_a: str, label_b: str) -> bool:
    """Convenience method, performs a sanity check to make sure the number of elements in two iterables is the same.  Logs an error if they do not match

    Args:
        a (Iterable): first `Iterable` to check
        b (Iterable): second `Iterable` to check
        label_a (str): The label to associate with `a` if an error is to be logged
        label_b (str): The label to associate with `b` if an error is to be logged

    Returns:
        bool: `True` if `a` and `b` have the same number of elements.
    """
    if not (result := (len_a := len(a)) == (len_b := len(b))):
        log.error("%s (%d) and %s differ (%d) in count!", label_a, len_a, label_b, len_b)

    return result


def _main() -> None:
    """Main driver, invoked when this file is run directly."""
    cli_parser = ArgumentParser(description="Program that renames tv episode orderings from dvd/absolute/streaming order to aired order")
    cli_parser.add_argument('--absolute', action='store_true', help="Treat input as absolute ordering")
    cli_parser.add_argument('--streaming', action='store_true', help="Treat input dirs as streaming ordering")

    cli_parser.add_argument('-l', action='store_true', help="Use lexigraphical sort instead of natural sort")
    cli_parser.add_argument('-s', action='store_true', help="Dry run, don't actually rename any files/dirs")
    cli_parser.add_argument('-i', action='store_true', help="Ignore errors mistmatch between episode count on thetvdb and the local filesystem")
    cli_parser.add_argument('-x', type=str, metavar="ext", help="The file extensions to target.  Defaults to .mkv, .mp4, and .avi")

    cli_parser.add_argument('series_id', type=int, help='The series id of the show in question on thetvdb')
    cli_parser.add_argument('root_dir', type=Path, nargs='?', default=Path("."), help='the directories to work on')
    args = cli_parser.parse_args()

    lg = logging.getLogger("tv_rename")
    lg.addHandler(RichHandler(rich_tracebacks=True))
    lg.setLevel(logging.DEBUG)

    if args.absolute:
        alt_type = "absolute"
    elif args.streaming:
        alt_type = "streaming"
    else:
        alt_type = "dvd"

    tvdb = fetch_tvdb()
    exts = {args.x} if args.x else VIDEO_EXTS
    pl = sorted([p for p in args.root_dir.glob("*/*") if p.is_file() and p.suffix.lower() in exts], key=None if args.l else natural_sort)
    el = _episodes_of(tvdb, args.series_id, alt_type)

    if not (_counts_match(pl, el, "episodes on local system", f"thetvdb {alt_type}") or args.i):
        return

    for i, p in enumerate(pl):
        el[i].local_path = p

    id_to_alt = {e.id: e for e in el}
    id_to_aired = {e.id: e for e in _episodes_of(tvdb, args.series_id)}

    if not (_counts_match(id_to_aired, id_to_alt, "thetvdb aired", f"thetvdb {alt_type}") or args.i):
        return

    if not args.s:
        for i in {e.season_number for e in id_to_aired.values()}:
            (args.root_dir / f"Season {i}").mkdir(exist_ok=True)

    for ep_id, aired_ep in id_to_aired.items():
        if not (alt_ep := id_to_alt.get(ep_id)):
            log.warning("%s does not exist in %s?!", aired_ep, alt_type)
            continue

        new_name = args.root_dir / f"Season {aired_ep.season_number}" / f"s{aired_ep.season_number:02}e{aired_ep.episode_number:02} --- {alt_ep.local_path.name}"
        log.info('Renaming "%s" to "%s"', alt_ep.local_path, new_name)

        if not args.s:
            alt_ep.local_path.rename(new_name)


if __name__ == "__main__":
    _main()
