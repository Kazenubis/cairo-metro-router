import pytest

from metro_router.matching import StationMatcher, UnknownStationError, normalize


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("El-Marg", "marg"),
        ("  AL shohadaa!! ", "shohadaa"),
        ("St. Teresa", "st teresa"),
        ("New El-Marg", "new marg"),
        ("El", "el"),
    ],
)
def test_normalize(raw, expected):
    assert normalize(raw) == expected


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("helwan", "Helwan"),
        ("SHOHADAA", "Al-Shohadaa"),
        ("el shohadaa", "Al-Shohadaa"),
        ("new marg", "New El-Marg"),
        ("sayeda zeinab", "Al-Sayeda Zeinab"),
        ("Tahrir", "Sadat"),
    ],
)
def test_resolve_is_forgiving(cairo, query, expected):
    matcher = StationMatcher(cairo.station_names(), cairo.aliases)
    assert matcher.resolve(query) == expected


def test_typo_gets_suggestions(cairo):
    matcher = StationMatcher(cairo.station_names(), cairo.aliases)
    with pytest.raises(UnknownStationError) as excinfo:
        matcher.resolve("Heliopolis Sqaure")
    assert excinfo.value.suggestions[0] == "Heliopolis Square"
    assert "Did you mean" in str(excinfo.value)


def test_nonsense_gets_no_suggestions(cairo):
    matcher = StationMatcher(cairo.station_names(), cairo.aliases)
    with pytest.raises(UnknownStationError) as excinfo:
        matcher.resolve("Atlantis")
    assert excinfo.value.suggestions == []
    assert "Did you mean" not in str(excinfo.value)


def test_names_that_normalize_the_same_are_rejected():
    with pytest.raises(ValueError):
        StationMatcher(["El-Marg", "Al Marg"])
