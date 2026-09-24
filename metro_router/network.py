"""Load the metro network from JSON and answer simple questions about it."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class NetworkError(ValueError):
    """Raised when network data is malformed or a line does not exist."""


@dataclass(frozen=True)
class Line:
    """One metro line: an id, a display name and its stations in order."""

    id: str
    name: str
    stations: tuple[str, ...]

    @property
    def terminals(self) -> tuple[str, str]:
        """The two end stations of the line."""
        return self.stations[0], self.stations[-1]

    def towards(self, from_station: str, to_station: str) -> str:
        """Return the terminal a train heads to when riding from one station to another."""
        start = self.stations.index(from_station)
        end = self.stations.index(to_station)
        return self.stations[-1] if end > start else self.stations[0]


@dataclass
class Network:
    """All lines plus optional alternative names for stations."""

    lines: dict[str, Line]
    aliases: dict[str, str] = field(default_factory=dict)

    def station_names(self) -> list[str]:
        """Every station once, in the order it first appears across the lines."""
        seen: dict[str, None] = {}
        for line in self.lines.values():
            for station in line.stations:
                seen.setdefault(station, None)
        return list(seen)

    def lines_at(self, station: str) -> list[str]:
        """Ids of the lines that stop at a station."""
        return [line.id for line in self.lines.values() if station in line.stations]

    def get_line(self, line_id: str) -> Line:
        """Look up a line by id, ignoring case (so '3b' finds '3B')."""
        for line in self.lines.values():
            if line.id.casefold() == line_id.strip().casefold():
                return line
        available = ", ".join(self.lines)
        raise NetworkError(f"Unknown line {line_id!r}. Available lines: {available}.")


def _parse_line(raw: dict[str, Any]) -> Line:
    """Validate one line entry from the JSON file."""
    line_id = str(raw.get("id", "")).strip()
    stations = raw.get("stations")
    if not line_id:
        raise NetworkError("Every line needs an 'id'.")
    if not isinstance(stations, list) or len(stations) < 2:
        raise NetworkError(f"Line {line_id} needs a list of at least two stations.")
    if len(set(stations)) != len(stations):
        raise NetworkError(f"Line {line_id} lists the same station twice.")
    return Line(id=line_id, name=str(raw.get("name", f"Line {line_id}")), stations=tuple(stations))


def network_from_dict(data: dict[str, Any]) -> Network:
    """Build a Network from already-parsed JSON data."""
    lines: dict[str, Line] = {}
    for raw in data.get("lines", []):
        line = _parse_line(raw)
        if line.id in lines:
            raise NetworkError(f"Line id {line.id} is used twice.")
        lines[line.id] = line
    if not lines:
        raise NetworkError("The network has no lines.")

    network = Network(lines=lines, aliases=dict(data.get("aliases", {})))
    known = set(network.station_names())
    for alias, target in network.aliases.items():
        if target not in known:
            raise NetworkError(f"Alias {alias!r} points to unknown station {target!r}.")
    return network


def load_network(path: Path = DATA_DIR / "stations.json") -> Network:
    """Read and validate the stations JSON file."""
    with open(path, encoding="utf-8") as handle:
        return network_from_dict(json.load(handle))
