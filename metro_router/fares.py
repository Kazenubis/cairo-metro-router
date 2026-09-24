"""Fare tiers based on how many stations a trip covers."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .network import DATA_DIR


class FareError(ValueError):
    """Raised when the fare table is malformed."""


@dataclass(frozen=True)
class FareTier:
    """Trips of up to `max_stations` cost `price`; None means 'any length'."""

    max_stations: int | None
    price: float


@dataclass(frozen=True)
class FareTable:
    """An ordered list of fare tiers in one currency."""

    currency: str
    tiers: tuple[FareTier, ...]

    def tier_for(self, stations: int) -> FareTier | None:
        """The tier a trip falls into, or None for a zero-station trip."""
        if stations < 0:
            raise ValueError("Number of stations cannot be negative.")
        if stations == 0:
            return None
        for tier in self.tiers:
            if tier.max_stations is None or stations <= tier.max_stations:
                return tier
        raise FareError(f"No fare tier covers {stations} stations.")

    def fare_for(self, stations: int) -> float:
        """Ticket price for a trip covering this many stations (0 if you don't travel)."""
        tier = self.tier_for(stations)
        return 0.0 if tier is None else tier.price


def fare_table_from_dict(data: dict[str, Any]) -> FareTable:
    """Build and validate a FareTable from parsed JSON."""
    tiers = tuple(FareTier(raw.get("max_stations"), float(raw["price"])) for raw in data.get("tiers", []))
    if not tiers:
        raise FareError("The fare table has no tiers.")
    if tiers[-1].max_stations is not None:
        raise FareError("The last fare tier must have max_stations set to null (no upper limit).")
    limits = [tier.max_stations for tier in tiers[:-1]]
    if None in limits or limits != sorted(set(limits)):
        raise FareError("Fare tiers must be listed with strictly increasing max_stations.")
    return FareTable(currency=str(data.get("currency", "EGP")), tiers=tiers)


def load_fares(path: Path = DATA_DIR / "fares.json") -> FareTable:
    """Read and validate the fares JSON file."""
    with open(path, encoding="utf-8") as handle:
        return fare_table_from_dict(json.load(handle))
