"""Utility for renaming TV episodes and Season directories"""

import logging
import re

from argparse import ArgumentParser
from pathlib import Path

from rich.logging import RichHandler

from .util import natural_sort, VIDEO_EXTS

log = logging.getLogger(__name__)


def _main() -> None:
    """Main driver, invoked when this file is run directly."""
    cli_parser = ArgumentParser(description="renames TV episodes or Season directories")
    cli_parser.add_argument('-s', action='store_true', help="Dry run, don't actually rename any files/dirs")
    cli_parser.add_argument('-d', action='store_true', help="Treat the input dir as a dir containg of season dirs to rename")
    cli_parser.add_argument('-l', action='store_true', help="Use lexigraphical sort instead of natural sort")
    cli_parser.add_argument('-x', type=str, metavar="ext", help="The file extension to get. Ignored if -d is passed.")
    cli_parser.add_argument('-n', type=int, metavar="season_number", help="The season number to rename episode files to. Ignored if -d is passed.")
    cli_parser.add_argument('-p', type=str, metavar="prefix", help="An optional prefix use at the beginning of episode filenames. Ignored if -d is passed.")
    cli_parser.add_argument('dirs', type=Path, nargs='*', help='the directories to work on')
    args = cli_parser.parse_args()

    log.addHandler(RichHandler(rich_tracebacks=True))
    log.setLevel(logging.INFO)

    sort_key = None if args.l else natural_sort

    if args.dirs:
        dl = args.dirs
    else:
        cwd = Path(".").resolve()
        dl = [cwd] if args.d else [d for d in cwd.iterdir() if d.is_dir() and re.match(r"(?i)Season \d+", d.name)]

    if not dl:
        log.error("No target directory was specified or you are not currently in an applicable tv/season directory")
        return
    elif args.n and len(dl) > 1:
        log.error("-n makes no sense with multiple Season dirs, abort")
        return

    for dir in dl:
        log.info("Now processing '%s'", dir)

        if args.d:
            l = [(s, dir / f"Season {i}") for i, s in enumerate(sorted([d for d in dir.iterdir() if d.is_dir()], key=sort_key), 1)]
        else:
            if not (season_cnt := int(dir.name.split(" ")[1]) if re.match(r"(?i)Season \d+", dir.name) else args.n):
                log.error("'%s' does not follow the standard format (e.g. 'Season 1') and you have not passed -n to override", dir)
                return

            exts = {args.x} if args.x else VIDEO_EXTS
            prefix = f"{args.p if args.p else dir.resolve(True).parent.name} - "
            l = [(s, dir / f"{prefix}s{season_cnt:02}e{i:02}{s.suffix}") for i, s in enumerate(sorted([f for f in dir.iterdir() if f.is_file() and f.suffix.lower() in exts], key=sort_key), 1)]

        for old_name, new_name in l:
            log.info('Renaming "%s" -> "%s"', old_name, new_name)
            if not args.s:
                old_name.rename(new_name)


if __name__ == "__main__":
    _main()
