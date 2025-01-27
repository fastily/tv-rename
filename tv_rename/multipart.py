"""Renames combined, multipart episodes into their aired ordering"""

import logging

from argparse import ArgumentParser
from pathlib import Path

from rich.logging import RichHandler

from .util import episodes_of, fetch_tvdb, natural_sort, VIDEO_EXTS


log = logging.getLogger(__name__)


class EpisodeGroup:
    """Associates a multipart group of episodes with the local file they are contained in"""

    def __init__(self, p: Path, group_season: int, mapped_eps: list[int]):
        """Initializer, creates a new `EpisodeGroup`

        Args:
            p (Path): The local file to associate with this `EpisodeGroup`
            group_season (int): The original season associated with `p`
            mapped_eps (list[int]): The episode numbers (from aired) to map to this `EpisodeGroup`
        """
        self.p = p
        self.group_season = group_season
        self.mapped_eps = mapped_eps

    def rename(self, dry_run: bool = False):
        """Renames the multipart episode file based on the episodes that are contained in it.

        Args:
            dry_run (bool, optional): Set `True` to perform a dry-run and only simulate renaming of files. Defaults to `False`.
        """
        eps = f"{self.mapped_eps[0]:02}" if len(self.mapped_eps) == 1 else f"{min(self.mapped_eps):02}-e{max(self.mapped_eps):02}"
        new_name = self.p.parent / f"{self.p.parent.parent.name} - s{self.group_season:02}e{eps}{self.p.suffix}"

        log.info('Now renaming "%s" to "%s"', self.p.name, new_name)
        if not dry_run:
            self.p.rename(new_name)


def _main() -> None:
    """Main driver, invoked when this file is run directly."""

    cli_parser = ArgumentParser(description="Program that renames multipart tv episodes into their aired ordering")
    cli_parser.add_argument('--absolute', action='store_true', help="Treat input as absolute ordering")
    cli_parser.add_argument('--streaming', action='store_true', help="Treat input dirs as streaming ordering")

    cli_parser.add_argument('-l', action='store_true', help="Use lexigraphical sort instead of natural sort")
    cli_parser.add_argument('-s', action='store_true', help="Dry run, don't actually rename any files/dirs")
    cli_parser.add_argument('-x', type=str, metavar="ext", help="The file extensions to target.  Defaults to .mkv, .mp4, and .avi")

    cli_parser.add_argument('series_id', type=int, help='The series id of the show in question on thetvdb')
    cli_parser.add_argument('root_dir', type=Path, nargs='?', default=Path("."), help='the series directory to work on.  Defaults to the current working directory')
    args = cli_parser.parse_args()

    lg = logging.getLogger()
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
    id_to_aired = {e.id: e for e in episodes_of(tvdb, args.series_id)}

    path_to_eps: dict[Path, EpisodeGroup] = {}
    pl_index = 0
    sn_num = ep_num = 1

    for e in episodes_of(tvdb, args.series_id, alt_type):
        if e.episode_number != ep_num or e.season_number != sn_num:
            ep_num = e.episode_number
            sn_num = e.season_number
            pl_index += 1

        mapped_ep_num = id_to_aired[e.id].episode_number
        if (curr_path := pl[pl_index]) not in path_to_eps:
            path_to_eps[curr_path] = EpisodeGroup(curr_path, sn_num, [mapped_ep_num])
        else:
            path_to_eps[curr_path].mapped_eps.append(mapped_ep_num)

    for eg in path_to_eps.values():
        eg.rename(args.s)


if __name__ == "__main__":
    _main()
