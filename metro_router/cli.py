"""Command-line interface: `python -m metro_router route|stations ...`."""

import argparse
import sys
from pathlib import Path

from .fares import FareError, load_fares
from .formatting import format_line, format_network, format_route
from .matching import UnknownStationError
from .network import DATA_DIR, NetworkError, load_network
from .router import DEFAULT_TRANSFER_PENALTY, NoRouteError, find_route


def _non_negative_float(text: str) -> float:
    try:
        value = float(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{text!r} is not a number") from None
    if value < 0:
        raise argparse.ArgumentTypeError("must be zero or more")
    return value


def build_parser() -> argparse.ArgumentParser:
    """Define the `route` and `stations` sub-commands."""
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--data-dir",
        type=Path,
        default=DATA_DIR,
        help="folder containing stations.json and fares.json (default: the bundled data/)",
    )

    parser = argparse.ArgumentParser(
        prog="metro_router",
        description="Find the best route between two Cairo Metro stations.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    route = commands.add_parser("route", parents=[common], help="plan a trip between two stations")
    route.add_argument("start", help="station you're leaving from")
    route.add_argument("end", help="station you're going to")
    route.add_argument(
        "--transfer-penalty",
        type=_non_negative_float,
        default=DEFAULT_TRANSFER_PENALTY,
        help=f"how many stops a change of line is 'worth' (default: {DEFAULT_TRANSFER_PENALTY:g})",
    )
    route.add_argument("--show-stations", action="store_true", help="list every station you pass through")

    stations = commands.add_parser("stations", parents=[common], help="list stations")
    stations.add_argument("--line", help="only show this line (e.g. 1, 2, 3, 3B)")
    return parser


def run(args: argparse.Namespace) -> str:
    """Execute a parsed command and return the text to print."""
    network = load_network(args.data_dir / "stations.json")
    if args.command == "stations":
        if args.line:
            return format_line(network, network.get_line(args.line))
        return format_network(network)

    fares = load_fares(args.data_dir / "fares.json")
    route = find_route(network, args.start, args.end, args.transfer_penalty, fares)
    return format_route(route, show_stations=args.show_stations)


def main(argv: list[str] | None = None) -> int:
    """Entry point; returns a process exit code."""
    args = build_parser().parse_args(argv)
    try:
        output = run(args)
    except (UnknownStationError, NoRouteError, NetworkError, FareError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(output)
    return 0
