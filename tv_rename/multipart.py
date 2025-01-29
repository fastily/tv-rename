"""Renames combined, multipart episodes into their aired ordering"""

import logging

from argparse import ArgumentParser
from pathlib import Path

from .util import configure_logging, episodes_of, fetch_tvdb, find_all_eps, shared_abs_stream_opts, resolve_alt_type, shared_cli_opts, shared_series_id_root_dir


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

    def rename(self, dry_run: bool = False) -> None:
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
    args = ArgumentParser(description="Program that renames multipart tv episodes into their aired ordering", parents=[shared_cli_opts(), shared_abs_stream_opts(), shared_series_id_root_dir()]).parse_args()
    configure_logging()

    alt_type = resolve_alt_type(args.absolute, args.streaming)
    tvdb = fetch_tvdb()
    pl = find_all_eps(args.root_dir, args.l, args.x)
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
