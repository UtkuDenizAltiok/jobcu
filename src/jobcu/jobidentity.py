"""Conservative remembered-job identity: source IDs before potentially ambiguous names."""

import json
import sqlite3
from collections import defaultdict
from collections.abc import Iterable, Iterator
from itertools import batched

from jobcu.dedupe import SOURCE_KIND_RANK, JobGroup, normal_city, normal_company, normal_title


def copy_key(source: str, vacancy: str) -> str:
    return f"copy:{source}:{vacancy}"


def fingerprints(group: JobGroup) -> list[tuple[str, str]]:
    entries = []
    for copy in group.copies:
        company, title = normal_company(copy.company), normal_title(copy.title)
        if company and title:
            key = f"job:{company}|{title}|{normal_city(copy.location_text)}"
            entries.append((key, (copy.country or "").upper()))
    return list(dict.fromkeys(entries))


def identity_keys(group: JobGroup) -> list[str]:
    copies = [copy_key(c.source, c.source_job_id) for c in group.copies if c.source_job_id]
    return list(dict.fromkeys([*copies, *(key for key, _ in fingerprints(group))]))


def rows(conn: sqlite3.Connection, query: str, values: Iterable) -> Iterator[sqlite3.Row]:
    """Bounded, parameterized lookups, including lower SQLite limits on another device."""
    size = min(900, conn.getlimit(sqlite3.SQLITE_LIMIT_VARIABLE_NUMBER))
    for batch in batched(dict.fromkeys(values), size, strict=False):
        yield from conn.execute(query.format(",".join("?" * len(batch))), batch)


class IdentityIndex:
    """One transaction's relevant keys; registering a group updates later batch matches."""

    def __init__(self):
        self.copies: dict[str, int] = {}
        self.names: dict[str, set[int]] = defaultdict(set)
        self.sources: dict[int, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
        self.countries: dict[int, set[str]] = defaultdict(set)
        self.ambiguous_names: dict[int, set[str]] = defaultdict(set)
        self.entries: dict[int, list[tuple[str, str]]] = {}

    def name_entries(self, group: JobGroup) -> list[tuple[str, str]]:
        if id(group) not in self.entries:
            self.entries[id(group)] = fingerprints(group)
        return self.entries[id(group)]

    def _batch_ambiguity(self, groups: list[JobGroup]) -> None:
        owners = defaultdict(lambda: defaultdict(set))
        for group in groups:
            for key, country in self.name_entries(group):
                owners[key][country].add(id(group))
        for key, countries in owners.items():
            all_owners = set().union(*countries.values())
            unknown = countries.get("", set())
            for country, group_ids in countries.items():
                matches = group_ids | unknown if country else all_owners
                if len(matches) > 1:
                    for group_id in group_ids:
                        self.ambiguous_names[group_id].add(key)

    @classmethod
    def load(cls, conn: sqlite3.Connection, groups: list[JobGroup]) -> "IdentityIndex":
        index = cls()
        keys = [copy_key(c.source, c.source_job_id) for g in groups for c in g.copies
                if c.source_job_id]
        for row in rows(conn, "SELECT key, job_id FROM job_keys WHERE key IN ({})", keys):
            index._add_copy(row["key"], row["job_id"])
        # Returning known copies needs no name search or historical-metadata load.
        uncertain = [group for group in groups if index._fast_id(group) is None]
        if not uncertain:
            return index
        index._batch_ambiguity(groups)
        names = [key for group in uncertain for key, _ in index.name_entries(group)]
        for row in rows(conn, "SELECT key, job_id, country FROM job_fingerprints "
                             "WHERE key IN ({})", names):
            index._add_name(row["key"], row["job_id"], row["country"])
        candidates = {index.copies[key] for group in uncertain for copy in group.copies
                      if copy.source_job_id and (key := copy_key(copy.source, copy.source_job_id))
                      in index.copies}
        candidates.update(job_id for key in names for job_id in index.names[key])
        for row in rows(conn, "SELECT key, job_id FROM job_keys WHERE job_id IN ({}) "
                             "AND key LIKE 'copy:%'", candidates):
            index._add_copy(row["key"], row["job_id"])
        for row in rows(conn, "SELECT key, job_id, country FROM job_fingerprints "
                             "WHERE job_id IN ({})", candidates):
            index._add_name(row["key"], row["job_id"], row["country"])
        legacy = [job_id for job_id in candidates if not index.countries[job_id]]
        for row in rows(conn, "SELECT job_id, card_json FROM job_cards WHERE job_id IN ({})",
                        legacy):
            try:
                country = json.loads(row["card_json"]).get("country")
            except (ValueError, AttributeError):
                continue
            if isinstance(country, str) and country:
                index.countries[row["job_id"]].add(country.upper())
        return index

    def _add_copy(self, key: str, job_id: int) -> None:
        self.copies.setdefault(key, job_id)
        _, source, vacancy = key.split(":", 2)
        if vacancy:
            self.sources[job_id][source].add(vacancy)

    def _add_name(self, key: str, job_id: int, country: str) -> None:
        self.names[key].add(job_id)
        if country:
            self.countries[job_id].add(country)

    def _ordered_copies(self, group: JobGroup):
        return sorted(group.copies, key=lambda c: (
            SOURCE_KIND_RANK.get(group.source_kinds.get(c.source, "aggregator"), 3),
            not c.description_is_complete,
        ))

    def _fast_id(self, group: JobGroup) -> int | None:
        if any(c.source_job_id and group.source_kinds.get(c.source) == "employer"
               and copy_key(c.source, c.source_job_id) not in self.copies for c in group.copies):
            return None
        return next((self.copies[key] for c in self._ordered_copies(group)
                     if c.source_job_id and (key := copy_key(c.source, c.source_job_id))
                     in self.copies), None)

    def _compatible(self, group: JobGroup, job_id: int, *, names_only: bool = False) -> bool:
        employer_ids: dict[str, set[str]] = defaultdict(set)
        for copy in group.copies:
            if copy.source_job_id and group.source_kinds.get(copy.source) == "employer":
                employer_ids[copy.source].add(copy.source_job_id)
        for source, vacancies in employer_ids.items():
            stored = self.sources[job_id].get(source)
            if stored and not vacancies.issubset(stored):
                return False
        countries = {c.country.upper() for c in group.copies if c.country}
        if names_only and countries and self.countries[job_id] and not (
                countries & self.countries[job_id]):
            return False
        return True

    def resolve(self, group: JobGroup) -> int | None:
        if (known := self._fast_id(group)) is not None:
            return known
        for copy in self._ordered_copies(group):
            job_id = self.copies.get(copy_key(copy.source, copy.source_job_id))
            if copy.source_job_id and job_id is not None and self._compatible(group, job_id):
                return job_id
        candidates = {job_id for key, _ in self.name_entries(group)
                      if key not in self.ambiguous_names[id(group)] for job_id in self.names[key]
                      if self._compatible(group, job_id, names_only=True)}
        # A title/employer/town match is insufficient when several vacancies share it.
        return next(iter(candidates)) if len(candidates) == 1 else None

    def register(self, group: JobGroup, job_id: int) -> None:
        for copy in group.copies:
            if copy.source_job_id:
                key = copy_key(copy.source, copy.source_job_id)
                owner = self.copies.get(key, job_id)
                self._add_copy(key, owner)
        for key, country in self.name_entries(group):
            self._add_name(key, job_id, country)
