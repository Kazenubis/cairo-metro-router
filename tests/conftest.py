"""Shared fixtures: the real bundled data and a tiny fake network."""

import pytest

from metro_router.fares import FareTable, load_fares
from metro_router.network import Network, load_network, network_from_dict


@pytest.fixture(scope="session")
def cairo() -> Network:
    return load_network()


@pytest.fixture(scope="session")
def fares() -> FareTable:
    return load_fares()


@pytest.fixture
def toy_network() -> Network:
    """A slow direct line versus a short trip that needs one change at M.

    Red:   A - B - C - D - E   (4 stops, no change)
    Blue:  A - M
    Green: M - E               (2 stops, one change at M)
    """
    return network_from_dict(
        {
            "lines": [
                {"id": "R", "name": "Red", "stations": ["A", "B", "C", "D", "E"]},
                {"id": "B", "name": "Blue", "stations": ["A", "M"]},
                {"id": "G", "name": "Green", "stations": ["M", "E"]},
            ]
        }
    )
