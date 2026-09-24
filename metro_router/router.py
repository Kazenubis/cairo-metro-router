"""Route finding: a (station, line) graph searched with Dijkstra."""

import heapq
import itertools
import math
from collections import defaultdict
from dataclasses import dataclass

from .fares import FareTable
from .matching import StationMatcher
from .network import Network

DEFAULT_TRANSFER_PENALTY = 3.0

Node = tuple[str, str]  # (station name, line id)
Edge = tuple[Node, float, bool]  # (neighbour, cost, is_transfer)
Graph = dict[Node, list[Edge]]


class NoRouteError(LookupError):
    """Raised when two stations are not connected."""


@dataclass(frozen=True)
class Leg:
    """A stretch of the trip spent on one line without changing trains."""

    line_id: str
    line_name: str
    stations: tuple[str, ...]
    towards: str

    @property
    def start(self) -> str:
        return self.stations[0]

    @property
    def end(self) -> str:
        return self.stations[-1]

    @property
    def stops(self) -> int:
        return len(self.stations) - 1


@dataclass(frozen=True)
class Route:
    """A full trip: its legs plus the totals a rider cares about."""

    start: str
    end: str
    legs: tuple[Leg, ...]
    fare: float | None = None
    currency: str = ""

    @property
    def stops(self) -> int:
        return sum(leg.stops for leg in self.legs)

    @property
    def transfers(self) -> int:
        return max(len(self.legs) - 1, 0)


def build_graph(network: Network, transfer_penalty: float = DEFAULT_TRANSFER_PENALTY) -> Graph:
    """Connect neighbouring stations (cost 1) and the same station across lines (the penalty)."""
    if transfer_penalty < 0:
        raise ValueError("Transfer penalty cannot be negative.")
    graph: defaultdict[Node, list[Edge]] = defaultdict(list)
    for line in network.lines.values():
        for here, there in itertools.pairwise(line.stations):
            graph[(here, line.id)].append(((there, line.id), 1.0, False))
            graph[(there, line.id)].append(((here, line.id), 1.0, False))
    for station in network.station_names():
        for from_line, to_line in itertools.permutations(network.lines_at(station), 2):
            graph[(station, from_line)].append(((station, to_line), transfer_penalty, True))
    return dict(graph)


def shortest_path(graph: Graph, sources: list[Node], targets: set[Node]) -> list[Node]:
    """Dijkstra from several start nodes to the nearest target node.

    Paths are compared by (cost, transfers), so on equal cost the one with
    fewer changes wins.
    """
    order = itertools.count()
    best: dict[Node, tuple[float, int]] = {node: (0.0, 0) for node in sources}
    previous: dict[Node, Node] = {}
    heap = [(0.0, 0, next(order), node) for node in sources]
    heapq.heapify(heap)
    settled: set[Node] = set()

    while heap:
        cost, transfers, _, node = heapq.heappop(heap)
        if node in settled:
            continue
        settled.add(node)
        if node in targets:
            return _walk_back(previous, node)
        for neighbour, weight, is_transfer in graph.get(node, []):
            candidate = (cost + weight, transfers + int(is_transfer))
            if neighbour not in settled and candidate < best.get(neighbour, (math.inf, 0)):
                best[neighbour] = candidate
                previous[neighbour] = node
                heapq.heappush(heap, (*candidate, next(order), neighbour))
    raise NoRouteError("No route connects those stations.")


def _walk_back(previous: dict[Node, Node], node: Node) -> list[Node]:
    path = [node]
    while path[-1] in previous:
        path.append(previous[path[-1]])
    return path[::-1]


def group_legs(network: Network, path: list[Node]) -> tuple[Leg, ...]:
    """Turn a node path into legs, one per line ridden."""
    runs: list[tuple[str, list[str]]] = []
    for station, line_id in path:
        if runs and runs[-1][0] == line_id:
            runs[-1][1].append(station)
        else:
            runs.append((line_id, [station]))

    legs = []
    for line_id, stations in runs:
        if len(stations) < 2:
            continue
        line = network.lines[line_id]
        legs.append(Leg(line_id, line.name, tuple(stations), line.towards(stations[0], stations[-1])))
    return tuple(legs)


def find_route(
    network: Network,
    start: str,
    end: str,
    transfer_penalty: float = DEFAULT_TRANSFER_PENALTY,
    fares: FareTable | None = None,
) -> Route:
    """Resolve two (possibly misspelled) station names and find the best route between them."""
    matcher = StationMatcher(network.station_names(), network.aliases)
    start_name, end_name = matcher.resolve(start), matcher.resolve(end)
    graph = build_graph(network, transfer_penalty)

    if start_name == end_name:
        legs: tuple[Leg, ...] = ()
    else:
        sources = [(start_name, line_id) for line_id in network.lines_at(start_name)]
        targets = {(end_name, line_id) for line_id in network.lines_at(end_name)}
        legs = group_legs(network, shortest_path(graph, sources, targets))

    stops = sum(leg.stops for leg in legs)
    return Route(
        start=start_name,
        end=end_name,
        legs=legs,
        fare=fares.fare_for(stops) if fares else None,
        currency=fares.currency if fares else "",
    )
