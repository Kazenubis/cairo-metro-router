"""Plain-text rendering of routes and station lists."""

from .network import Line, Network
from .router import Route


def _plural(count: int, word: str) -> str:
    return f"{count} {word}" if count == 1 else f"{count} {word}s"


def format_money(amount: float, currency: str) -> str:
    """'15 EGP' for whole amounts, '7.50 EGP' otherwise."""
    value = f"{amount:.0f}" if float(amount).is_integer() else f"{amount:.2f}"
    return f"{value} {currency}".strip()


def format_route(route: Route, show_stations: bool = False) -> str:
    """Render a route as a readable, indented plain-text block."""
    title = f"{route.start}  ->  {route.end}"
    lines = [title, "=" * len(title), ""]

    if not route.legs:
        lines.append(f"  You're already at {route.start}. No travel needed.")
        lines.append("")
    for index, leg in enumerate(route.legs):
        if index:
            lines.append(f"  ~ change at {leg.start} ~")
            lines.append("")
        label = f"[{leg.line_name}]"
        lines.append(f"  {label} {leg.start} -> {leg.end}")
        lines.append(f"  {' ' * len(label)} towards {leg.towards}, {_plural(leg.stops, 'stop')}")
        if show_stations:
            for station in leg.stations[1:-1]:
                lines.append(f"  {' ' * len(label)}   . {station}")
        lines.append("")

    summary = f"Stops: {route.stops}   Transfers: {route.transfers}"
    if route.fare is not None:
        summary += f"   Fare: {format_money(route.fare, route.currency)}"
    lines.append("-" * len(title))
    lines.append(summary)
    return "\n".join(lines)


def format_line(network: Network, line: Line) -> str:
    """Numbered station list for one line, marking interchanges."""
    first, last = line.terminals
    lines = [f"{line.name}: {first} <-> {last} ({len(line.stations)} stations)", ""]
    width = max(len(station) for station in line.stations)
    for number, station in enumerate(line.stations, start=1):
        others = [other for other in network.lines_at(station) if other != line.id]
        note = "  change: " + ", ".join(f"Line {other}" for other in others) if others else ""
        lines.append(f"  {number:>2}  {station:<{width}}{note}".rstrip())
    return "\n".join(lines)


def format_network(network: Network) -> str:
    """Every line, one after the other."""
    return "\n\n".join(format_line(network, line) for line in network.lines.values())
