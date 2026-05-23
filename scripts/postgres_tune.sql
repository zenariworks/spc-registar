-- Postgres tuning for the spc-registar production box.
--
-- Box: 7.6 GB RAM, 4 CPUs, SSD storage, 1 active production tenant.
-- Postgres: 16.13 (Ubuntu 16.13-0ubuntu0.24.04.1)
--
-- All changes go into postgresql.auto.conf via ALTER SYSTEM. To revert, run
-- ALTER SYSTEM RESET <name>; (or RESET ALL to drop every override).
--
-- Apply with:
--   sudo -u postgres psql -d crkva_db -f scripts/postgres_tune.sql
--   sudo systemctl restart postgresql      # shared_preload_libraries + shared_buffers
--
-- After Postgres is back up, re-run the bottom block to create the
-- pg_stat_statements extension and set its parameters (they cannot be set
-- before the library is loaded).

-- ============================================================
-- Memory: ~20% of RAM to shared_buffers, ~65% as OS-cache hint
-- ============================================================
ALTER SYSTEM SET shared_buffers = '1536MB';      -- restart required
ALTER SYSTEM SET effective_cache_size = '5GB';
ALTER SYSTEM SET work_mem = '32MB';              -- per-sort/hash budget
ALTER SYSTEM SET maintenance_work_mem = '512MB'; -- speeds CREATE INDEX + VACUUM

-- ============================================================
-- SSD cost model (Postgres defaults assume spinning rust)
-- ============================================================
ALTER SYSTEM SET random_page_cost = '1.1';
ALTER SYSTEM SET effective_io_concurrency = '200';

-- ============================================================
-- Checkpoint smoothing (less write-spike on bulk inserts)
-- ============================================================
ALTER SYSTEM SET max_wal_size = '4GB';
ALTER SYSTEM SET min_wal_size = '1GB';
ALTER SYSTEM SET checkpoint_completion_target = '0.9';

-- ============================================================
-- pg_stat_statements: query-level observability
-- ============================================================
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';  -- restart required


-- ============================================================
-- Run the block below AFTER restarting Postgres (so the
-- pg_stat_statements library is loaded and its params exist).
-- ============================================================
-- CREATE EXTENSION IF NOT EXISTS pg_stat_statements WITH SCHEMA public;
-- ALTER SYSTEM SET "pg_stat_statements.track" = 'all';
-- ALTER SYSTEM SET "pg_stat_statements.max"   = '5000';
-- SELECT pg_reload_conf();


-- ============================================================
-- Useful queries once pg_stat_statements is live
-- ============================================================
-- Top-10 slowest queries by mean execution time:
--   SELECT round(mean_exec_time::numeric, 2) AS ms, calls,
--          left(query, 120) AS query
--   FROM pg_stat_statements
--   WHERE query NOT LIKE '%pg_stat%'
--   ORDER BY mean_exec_time DESC LIMIT 10;
--
-- Top-10 by total time (real cost driver — slow * frequent):
--   SELECT round(total_exec_time::numeric/1000, 2) AS total_s, calls,
--          round(mean_exec_time::numeric, 2) AS mean_ms,
--          left(query, 120) AS query
--   FROM pg_stat_statements
--   ORDER BY total_exec_time DESC LIMIT 10;
--
-- Reset the stats after a baseline period:
--   SELECT pg_stat_statements_reset();
