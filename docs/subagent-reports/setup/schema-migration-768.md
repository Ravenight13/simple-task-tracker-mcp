# Database Schema Migration: 384-dim → 768-dim Vectors

**Date:** November 1, 2025
**Executed by:** Claude Code (Subagent)
**Task:** Schema migration for embedding model upgrade
**Status:** SUCCESS ✅

---

## Executive Summary

Successfully migrated the `documents` table from 384-dimensional to 768-dimensional vector embeddings to support the upgraded embedding model (all-mpnet-base-v2). All existing data was truncated as confirmed by user, and the HNSW index was rebuilt for the new vector dimensions.

**Total Execution Time:** ~3 seconds
**Downtime:** None (development environment)
**Errors:** 0
**Warnings:** 0

---

## Pre-Migration State

**Before Migration:**
- Document count: 334
- Chunks with embeddings: 334
- Embedding dimension: 384 (implicit from previous schema)
- Index type: HNSW with vector_cosine_ops

**Database Connection:**
- Host: ep-damp-waterfall-a4rkz9eu-pooler.us-east-1.aws.neon.tech
- Database: neondb
- Connection: Pooled (Neon serverless)

---

## Migration Steps Executed

### Step 1: Verify Current State
```sql
SELECT COUNT(*) as current_doc_count FROM documents;
-- Result: 334 documents

SELECT COUNT(*) as current_chunks FROM documents WHERE embedding IS NOT NULL;
-- Result: 334 chunks with embeddings
```

### Step 2: Truncate Table
```sql
TRUNCATE TABLE documents CASCADE;
-- Result: SUCCESS - All 334 rows deleted
```

### Step 3: Alter Embedding Column
```sql
ALTER TABLE documents
ALTER COLUMN embedding TYPE vector(768);
-- Result: SUCCESS - Column type changed
```

### Step 4: Drop Old Index
```sql
DROP INDEX IF EXISTS idx_documents_embedding;
-- Result: SUCCESS - Old index dropped
```

### Step 5: Create New HNSW Index
```sql
CREATE INDEX idx_documents_embedding
ON documents
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
-- Result: SUCCESS - New HNSW index created for 768-dim vectors
```

---

## Post-Migration State

**After Migration:**
- Document count: 0 (as expected - table truncated)
- Embedding dimension: **768 (verified via atttypmod)**
- Index type: HNSW with vector_cosine_ops
- Index parameters: m=16, ef_construction=64

**Schema Verification:**
```sql
SELECT column_name, data_type, udt_name
FROM information_schema.columns
WHERE table_name = 'documents' AND column_name = 'embedding';

-- Result:
-- column_name | data_type    | udt_name
-- embedding   | USER-DEFINED | vector
```

**Dimension Verification:**
```sql
SELECT atttypmod FROM pg_attribute
WHERE attrelid = 'documents'::regclass AND attname = 'embedding';

-- Result: 768 ✅
```

**Index Verification:**
```sql
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'documents';

-- Result:
-- idx_documents_embedding | CREATE INDEX ... USING hnsw (embedding vector_cosine_ops)
--                           WITH (m='16', ef_construction='64')
```

---

## Index Configuration Analysis

**HNSW Index Parameters:**
- **m = 16:** Number of bi-directional links per node (good balance for ~2,600 chunks)
- **ef_construction = 64:** Size of dynamic candidate list during construction (2x-4x of m is optimal)

**Performance Expectations:**
- Search latency: <100ms for top-10 results
- Index build time: ~30 seconds for 2,600 chunks
- Memory overhead: ~40MB (768-dim × 2,600 chunks × 4 bytes × 16 links)

**Why HNSW over IVFFlat:**
- Better for smaller datasets (<1M vectors)
- No training data required
- Faster query times (<100ms vs 200-500ms)
- Better recall at high speeds

---

## Database Objects Status

**All Indexes on `documents` table:**
1. `documents_pkey` - UNIQUE B-tree on `id` (primary key)
2. `idx_documents_source` - B-tree on `source_path` (file path lookups)
3. `idx_documents_metadata` - GIN on `metadata` (JSONB queries)
4. `idx_documents_embedding` - HNSW on `embedding` (vector similarity) ✅ **UPDATED**

---

## Execution Timeline

| Step | Duration | Status |
|------|----------|--------|
| 1. Check current state | <1s | ✅ SUCCESS |
| 2. Truncate table | <1s | ✅ SUCCESS |
| 3. Alter column type | <1s | ✅ SUCCESS |
| 4. Drop old index | <1s | ✅ SUCCESS |
| 5. Create new HNSW index | <1s | ✅ SUCCESS |
| 6. Verify schema | <1s | ✅ SUCCESS |
| **TOTAL** | **~3s** | **✅ SUCCESS** |

---

## Next Steps

### Immediate (Required)
1. **Re-run ingestion script** with new 768-dim embeddings
   - Expected: ~2,600 chunks from 343 markdown files
   - Estimated time: 45-60 minutes (768-dim encoding slower than 384-dim)
   - Command: `python scripts/ingest_knowledge_base.py`

2. **Verify embedding quality**
   - Test semantic search with sample queries
   - Compare recall vs 384-dim baseline (expect 10-15% improvement)

3. **Monitor index build**
   - Watch for index creation during ingestion
   - Verify HNSW index completes successfully

### Follow-up (Recommended)
1. **Benchmark search performance**
   - Target: <500ms for semantic_search tool
   - Measure: avg, p50, p95, p99 latency

2. **Validate search accuracy**
   - Test with known vendor queries
   - Test with team member lookups
   - Verify metadata filtering works

3. **Update documentation**
   - Mark Task 23 as COMPLETE
   - Update ARCHITECTURE_SPEC.md with 768-dim
   - Update .env.example with new EMBEDDING_DIMENSION

---

## Validation Checklist

- [x] Database connection successful
- [x] Pre-migration state captured (334 docs)
- [x] Table truncated successfully (0 rows)
- [x] Embedding column altered to vector(768)
- [x] Old index dropped
- [x] New HNSW index created with correct parameters
- [x] Schema verified (atttypmod = 768)
- [x] Index verified (HNSW with vector_cosine_ops)
- [x] No errors or warnings
- [x] Post-migration state documented

---

## Technical Notes

### Why TRUNCATE CASCADE?
- Ensures any dependent objects are handled gracefully
- In this schema, no foreign key dependencies exist
- Safe operation for clean slate migration

### Why ALTER TYPE works instantly?
- pgvector stores vectors as binary data
- Changing vector dimension doesn't require data rewrite when table is empty
- Only metadata update required (atttypmod field)

### Why rebuild index?
- HNSW index is dimension-specific
- Cannot reuse 384-dim index for 768-dim vectors
- Must drop and recreate for correct graph structure

### Memory Considerations
**Per-vector storage:**
- 384-dim: 1,536 bytes (384 × 4 bytes per float)
- 768-dim: 3,072 bytes (768 × 4 bytes per float)
- **Increase: 2x storage per vector**

**Expected database size:**
- 2,600 chunks × 3,072 bytes = ~8 MB (vector data only)
- Plus metadata, content, indexes = ~50-100 MB total
- Well within Neon free tier limits (512 MB)

---

## Success Metrics

- [x] Migration completed without errors
- [x] Schema matches target specification (768-dim)
- [x] HNSW index configured optimally
- [x] Table ready for re-ingestion
- [x] Zero data loss (intentional truncate)
- [x] Zero downtime (dev environment)

---

## Related Files

**Modified:**
- Database schema: `documents.embedding` column (384 → 768 dimensions)
- Index: `idx_documents_embedding` (rebuilt for 768-dim)

**To Update:**
- `scripts/ingest_knowledge_base.py` - Re-run with new embeddings
- `src/embeddings.py` - Already updated (uses all-mpnet-base-v2)
- `.env` - Already updated (EMBEDDING_DIMENSION=768)

**Documentation:**
- This report: `docs/subagent-reports/setup/schema-migration-768.md`
- Task tracking: Task 23 (schema migration) → COMPLETE

---

## Commit Message

```
feat: migrate database schema to 768-dim vectors

- ALTER documents.embedding from vector(384) to vector(768)
- Rebuild HNSW index with m=16, ef_construction=64
- Truncate existing 384-dim embeddings (334 docs)
- Verified schema: atttypmod=768, index type=HNSW
- Ready for re-ingestion with all-mpnet-base-v2 embeddings

Supports embedding model upgrade (Task 22)
Schema migration complete (Task 23)
Next: Re-run ingestion script

Execution time: ~3 seconds
Status: SUCCESS ✅
```

---

**Report Generated:** November 1, 2025
**Database State:** READY for re-ingestion
**Migration Status:** COMPLETE ✅
**Next Action:** Run `python scripts/ingest_knowledge_base.py`
