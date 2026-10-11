"""Resolve exact accession strings against an injected local source."""
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class SourceResult:
    code: str
    value: str | None = None


class SourceError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class CacheEntry:
    found: bool
    value: str | None
    stored_at: int
    ttl: int


class ResolveAccession:
    def __init__(self, source: Callable[[str], SourceResult], clock: Callable[[], int]):
        self._source = source
        self._clock = clock
        self._cache: dict[str, CacheEntry] = {}

    def snapshot(self) -> dict[str, CacheEntry]:
        """Return a diagnostic copy; callers cannot mutate the resolver's mapping."""
        return dict(self._cache)

    def resolve(self, key: object) -> dict:
        # TODO(AC-06): reject invalid input before consulting dependencies.
        now = self._clock()
        if not isinstance(key, str) or not 1 <= len(key) <= 24:
            return {'found': False, 'value': None, 'code': 'INVALID_ACCESSION'}
        # TODO(AC-01, AC-03, AC-05): implement the cache decision and fill rules.
        try:
            result = self._source(key)
        except SourceError:
            # TODO(AC-02, AC-04): preserve source failures instead of reporting absence.
            result = SourceResult('NOT_FOUND')
        found = result.code == 'FOUND'
        self._cache[key] = CacheEntry(found, result.value, now, 1000)
        return {'found': found, 'value': result.value,
                'code': None if found else 'NOT_FOUND'}
