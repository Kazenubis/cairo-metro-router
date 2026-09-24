import pytest

from metro_router.fares import FareError, fare_table_from_dict

SAMPLE = {
    "currency": "EGP",
    "tiers": [
        {"max_stations": 9, "price": 8},
        {"max_stations": 16, "price": 10},
        {"max_stations": 23, "price": 15},
        {"max_stations": None, "price": 20},
    ],
}


@pytest.mark.parametrize(
    ("stations", "price"),
    [(0, 0), (1, 8), (9, 8), (10, 10), (16, 10), (17, 15), (23, 15), (24, 20), (60, 20)],
)
def test_fare_tier_boundaries(stations, price):
    table = fare_table_from_dict(SAMPLE)
    assert table.fare_for(stations) == price


def test_negative_station_count_is_rejected():
    with pytest.raises(ValueError):
        fare_table_from_dict(SAMPLE).fare_for(-1)


def test_tiers_must_increase():
    broken = {"tiers": [{"max_stations": 16, "price": 10}, {"max_stations": 9, "price": 8}, {"max_stations": None, "price": 20}]}
    with pytest.raises(FareError):
        fare_table_from_dict(broken)


def test_last_tier_must_be_open_ended():
    with pytest.raises(FareError):
        fare_table_from_dict({"tiers": [{"max_stations": 9, "price": 8}]})
