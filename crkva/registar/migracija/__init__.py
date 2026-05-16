"""Shared utilities used by the migracija_* management commands.

Each migration was duplicating the same name cleaning, date parsing, lookup
caching, and Osoba get-or-create logic — often with subtly different
semantics. This package consolidates one canonical implementation per concern
so a bug fixed here is fixed everywhere.

Modules:
    helpers      pure string / date / time helpers (no DB access)
    osoba_repo   single canonical find_or_create_osoba
    cache        LookupCache class for memoised get_or_create of small lookups
    address      Adresa creation helpers
    errors       structured skip/error logging
"""
