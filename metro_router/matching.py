"""Forgiving station-name lookup with 'did you mean' suggestions."""

import difflib
import re
from collections.abc import Iterable, Mapping

_IGNORED_PREFIXES = {"el", "al"}


class UnknownStationError(LookupError):
    """Raised when a station name cannot be matched."""

    def __init__(self, query: str, suggestions: list[str]) -> None:
        self.query = query
        self.suggestions = suggestions
        message = f"Unknown station {query!r}."
        if suggestions:
            message += " Did you mean: " + ", ".join(suggestions) + "?"
        super().__init__(message)


def normalize(name: str) -> str:
    """Lower-case a name, drop punctuation and the 'el'/'al' articles.

    'El-Marg', 'el marg' and 'Marg!' all become 'marg'.
    """
    words = re.sub(r"[^\w\s]|_", " ", name.casefold()).split()
    kept = [word for word in words if word not in _IGNORED_PREFIXES]
    return " ".join(kept or words)


class StationMatcher:
    """Maps user input to canonical station names."""

    def __init__(self, names: Iterable[str], aliases: Mapping[str, str] | None = None) -> None:
        self._index: dict[str, str] = {}
        for name in names:
            self._add(name, name)
        for alias, target in (aliases or {}).items():
            self._add(alias, target)

    def _add(self, spelling: str, canonical: str) -> None:
        key = normalize(spelling)
        existing = self._index.get(key)
        if existing is not None and existing != canonical:
            raise ValueError(f"{spelling!r} is ambiguous: matches {existing!r} and {canonical!r}.")
        self._index[key] = canonical

    def resolve(self, query: str) -> str:
        """Return the canonical name for a query or raise UnknownStationError."""
        match = self._index.get(normalize(query))
        if match is None:
            raise UnknownStationError(query, self.suggest(query))
        return match

    def suggest(self, query: str, limit: int = 3) -> list[str]:
        """Closest canonical names to a query, best first, without duplicates."""
        close = difflib.get_close_matches(normalize(query), list(self._index), n=limit * 2, cutoff=0.6)
        suggestions: list[str] = []
        for key in close:
            name = self._index[key]
            if name not in suggestions:
                suggestions.append(name)
        return suggestions[:limit]
