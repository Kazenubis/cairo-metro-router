import pytest

from metro_router.matching import UnknownStationError
from metro_router.network import network_from_dict
from metro_router.router import NoRouteError, build_graph, find_route


def test_same_line_route_has_one_leg_and_no_transfers(cairo):
    route = find_route(cairo, "Helwan", "Maadi")

    assert [leg.line_id for leg in route.legs] == ["1"]
    assert route.stops == 10
    assert route.transfers == 0
    assert route.legs[0].towards == "New El-Marg"


def test_direction_flips_when_travelling_the_other_way(cairo):
    route = find_route(cairo, "Maadi", "Helwan")

    assert route.legs[0].towards == "Helwan"
    assert route.legs[0].stations[0] == "Maadi"


def test_route_with_one_transfer(cairo):
    route = find_route(cairo, "Dokki", "Heliopolis Square")

    assert route.transfers == 1
    first, second = route.legs
    assert (first.line_id, first.end, first.towards) == ("2", "Attaba", "Shubra El-Kheima")
    assert (second.line_id, second.start, second.towards) == ("3", "Attaba", "Adly Mansour")
    assert (first.stops, second.stops) == (4, 10)


def test_transfer_penalty_changes_the_chosen_route(toy_network):
    with_penalty = find_route(toy_network, "A", "E", transfer_penalty=3)
    without_penalty = find_route(toy_network, "A", "E", transfer_penalty=0)

    assert [leg.line_id for leg in with_penalty.legs] == ["R"]
    assert with_penalty.stops == 4
    assert [leg.line_id for leg in without_penalty.legs] == ["B", "G"]
    assert without_penalty.stops == 2
    assert without_penalty.transfers == 1


def test_equal_cost_prefers_fewer_transfers(toy_network):
    # Penalty 2: Red costs 4, Blue+Green costs 2 + 2 = 4. The direct ride should win the tie.
    route = find_route(toy_network, "A", "E", transfer_penalty=2)
    assert route.transfers == 0


def test_same_start_and_end(cairo, fares):
    route = find_route(cairo, "Sadat", "tahrir", fares=fares)

    assert route.legs == ()
    assert route.stops == 0
    assert route.transfers == 0
    assert route.fare == 0


def test_unknown_station_raises_with_suggestions(cairo):
    with pytest.raises(UnknownStationError) as excinfo:
        find_route(cairo, "Helwn", "Attaba")
    assert "Helwan" in excinfo.value.suggestions


def test_fare_is_attached_to_route(cairo, fares):
    route = find_route(cairo, "Helwan", "Maadi", fares=fares)
    assert route.fare == 10
    assert route.currency == "EGP"


def test_disconnected_stations_raise_no_route():
    island = network_from_dict(
        {"lines": [{"id": "X", "stations": ["P", "Q"]}, {"id": "Y", "stations": ["S", "T"]}]}
    )
    with pytest.raises(NoRouteError):
        find_route(island, "P", "T")


def test_negative_transfer_penalty_is_rejected(toy_network):
    with pytest.raises(ValueError):
        build_graph(toy_network, transfer_penalty=-1)


def test_bundled_data_has_the_main_interchanges(cairo):
    assert cairo.lines_at("Sadat") == ["1", "2"]
    assert cairo.lines_at("Al-Shohadaa") == ["1", "2"]
    assert cairo.lines_at("Nasser") == ["1", "3"]
    assert cairo.lines_at("Attaba") == ["2", "3"]
    assert cairo.lines_at("Cairo University") == ["2", "3B"]
