-- TraceChain: Add semantic grounding columns
-- Migration is idempotent (uses IF NOT EXISTS / conditional UPDATE)

-- 1. Add nullable relevance score columns to claims
ALTER TABLE claims ADD COLUMN IF NOT EXISTS query_relevance DOUBLE PRECISION;
ALTER TABLE claims ADD COLUMN IF NOT EXISTS evidence_support DOUBLE PRECISION;

-- 2. Add nullable source_type column to sources
ALTER TABLE sources ADD COLUMN IF NOT EXISTS source_type VARCHAR(10);

-- 3. Backfill known demo sources
UPDATE sources
SET source_type = 'demo'
WHERE id IN ('SOURCE-001', 'SOURCE-002')
  AND (source_type IS NULL OR source_type != 'demo');
