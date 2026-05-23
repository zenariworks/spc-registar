"""Source abstractions for seed_* commands.

A Source yields dict rows for a target model. Same iteration contract
regardless of where the data comes from (mock generator / DBF staging /
JSON fixture).

Currently:
- MockSource is fully implemented — used by seed_* commands when
  load_data --from mock is invoked.
- DbfSource and FixtureSource are stubs for now; the existing
  migracija_* + load_dbf commands handle the real DBF flow until those
  are unified in a follow-up.
"""
from __future__ import annotations

from collections.abc import Iterator
from typing import Any


class Source:
    """Base contract: produce iter of dicts for a given entity name."""

    def iter_rows(self, entity: str) -> Iterator[dict[str, Any]]:
        raise NotImplementedError


class MockSource(Source):
    """Generates synthetic data via crkva.registar.mock.generators.

    Stateful: pass `count` to scale the dataset. Constraints in
    constraints.py are applied by the SEEDERS (not here) so source
    stays a simple iterator.
    """

    def __init__(self, count: int = 100, seed: int | None = None):
        self.count = count
        self.seed = seed

    def iter_rows(self, entity: str) -> Iterator[dict[str, Any]]:
        # Seeders call this with entity-specific routing.
        # Concrete dict shapes live in the seeders themselves so
        # source stays decoupled from model schemas.
        raise NotImplementedError(
            "MockSource.iter_rows is generator-routed in seeders — "
            "use seeders directly."
        )


class FixtureSource(Source):
    """Load JSON fixture file (Django dumpdata format). STUB."""

    def __init__(self, path: str):
        self.path = path

    def iter_rows(self, entity: str) -> Iterator[dict[str, Any]]:
        raise NotImplementedError("FixtureSource not yet implemented")


class DbfSource(Source):
    """Read hsp_* staging tables (after load_dbf). STUB.

    The existing migracija_* commands handle DBF→model conversion
    today. This source will replace them in a follow-up commit.
    """

    def iter_rows(self, entity: str) -> Iterator[dict[str, Any]]:
        raise NotImplementedError(
            "DbfSource not yet implemented — use migracija_* commands "
            "or the importuj_dbf orchestrator instead."
        )
