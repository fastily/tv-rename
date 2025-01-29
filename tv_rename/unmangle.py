"""Program that renames dvd/streaming/absolute ordered episodes to aired ordering based using data from TheTVDB"""

import logging

from argparse import ArgumentParser
from collections.abc import Iterable

from .util import configure_logging, episodes_of, fetch_tvdb, find_all_eps, shared_abs_stream_opts, resolve_alt_type, shared_cli_opts, shared_series_id_root_dir


log = logging.getLogger(__name__)


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
    cli_parser = ArgumentParser(description="Program that renames tv episode orderings from dvd/absolute/streaming order to aired order", parents=[shared_cli_opts(), shared_abs_stream_opts(), shared_series_id_root_dir()])
    cli_parser.add_argument('-i', action='store_true', help="Ignore errors mistmatch between episode count on thetvdb and the local filesystem")
    args = cli_parser.parse_args()

    configure_logging()

    alt_type = resolve_alt_type(args.absolute, args.streaming)
    tvdb = fetch_tvdb()
    pl = find_all_eps(args.root_dir, args.l, args.x)
    el = episodes_of(tvdb, args.series_id, alt_type)

    if not (_counts_match(pl, el, "episodes on local system", f"thetvdb {alt_type}") or args.i):
        return

    for i, p in enumerate(pl):
        el[i].local_path = p

    id_to_alt = {e.id: e for e in el}
    id_to_aired = {e.id: e for e in episodes_of(tvdb, args.series_id)}

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
