# Timestamp Standardization Analysis Report

**Date:** 2025-10-27 15:30 UTC
**Task:** v0.2.0 Enhancement #1 - Standardize Timestamps to ISO 8601
**Agent:** python-wizard
**Project:** Task MCP Server

---

## Executive Summary

### Problem Identified
Mixed timestamp formats in API responses causing developer experience issues:
- **ISO 8601 format** (Python explicit): `2025-10-27T09:28:28.263154` (with 'T' separator and microseconds)
- **SQLite CURRENT_TIMESTAMP format**: `2025-10-27 14:28:28` (space separator, no microseconds)

### Root Cause
Two distinct timestamp generation methods:
1. **Python explicit timestamps**: `datetime.now().isoformat()` → ISO 8601 compliant
2. **SQLite DEFAULT CURRENT_TIMESTAMP**: SQLite's built-in function → Non-ISO 8601 format

### Impact
- **created_at**: Uses SQLite DEFAULT → Non-ISO 8601 format
- **updated_at**: Uses Python explicit → ISO 8601 format (when updated)
- **completed_at**: Uses Python explicit → ISO 8601 format
- **deleted_at**: Uses Python explicit → ISO 8601 format
- **master.db timestamps**: All use Python explicit → ISO 8601 format

---

## Detailed Analysis

### Files Analyzed

#### 1. `/src/task_mcp/server.py`
**Purpose:** FastMCP tool implementations with timestamp operations

**Timestamp Operations Found:**

| Line | Context | Format | Field |
|------|---------|--------|-------|
| 359 | `update_task()` - updated_at | `datetime.now().isoformat()` | `updated_at` |
| 364 | `update_task()` - completed_at | `datetime.now().isoformat()` | `completed_at` |
| 655 | `delete_task()` - soft delete | `datetime.now().isoformat()` | `deleted_at` |
| 796 | `cleanup_deleted_tasks()` - cutoff calculation | `(datetime.now() - timedelta(days)).isoformat()` | Comparison |

**Analysis:**
- All explicit timestamp assignments use `.isoformat()` ✓
- These timestamps are **already ISO 8601 compliant** ✓
- No changes needed in `server.py`

#### 2. `/src/task_mcp/master.py`
**Purpose:** Master database operations for project registry

**Timestamp Operations Found:**

| Line | Context | Format | Field |
|------|---------|--------|-------|
| 119 | `register_project()` - update last_accessed | `datetime.now().isoformat()` | `last_accessed` |
| 131 | `register_project()` - insert created_at | `datetime.now().isoformat()` | `created_at` |
| 132 | `register_project()` - insert last_accessed | `datetime.now().isoformat()` | `last_accessed` |

**Analysis:**
- All explicit timestamp assignments use `.isoformat()` ✓
- Master database timestamps are **already ISO 8601 compliant** ✓
- No changes needed in `master.py`

#### 3. `/src/task_mcp/database.py`
**Purpose:** Database operations and schema initialization

**Critical Finding: SQLite DEFAULT Values**

| Line | Context | Issue |
|------|---------|-------|
| 92 | Schema: `created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP` | **Uses SQLite's CURRENT_TIMESTAMP** |
| 93 | Schema: `updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP` | **Uses SQLite's CURRENT_TIMESTAMP** |

**Problem:**
- When `INSERT INTO tasks` is called without explicit timestamp values, SQLite's `CURRENT_TIMESTAMP` function is invoked
- SQLite's `CURRENT_TIMESTAMP` returns: `2025-10-27 14:28:28` (UTC time, space separator, no microseconds)
- This violates ISO 8601 format which requires 'T' separator

**Solution:**
- Remove `DEFAULT CURRENT_TIMESTAMP` from schema
- Application code in `server.py` must provide explicit timestamps
- Ensures all timestamps use Python's `.isoformat()` method

#### 4. `/src/task_mcp/models.py`
**Purpose:** Pydantic V2 data models with validation

**Analysis:**
- Lines 228-239: Timestamp fields defined as `Optional[datetime]`
- Line 307: `completed_at = datetime.utcnow()` in model validator
- **Issue Found:** Line 307 should use `.isoformat()` for consistency
- Pydantic's `strict=False` allows coercion of both formats (backward compatible)

---

## Implementation Plan

### Changes Required

#### 1. **database.py** (Schema Fix)
**Location:** Lines 92-93

**BEFORE:**
```python
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
```

**AFTER:**
```python
created_at TIMESTAMP,
updated_at TIMESTAMP,
```

**Rationale:** Remove SQLite DEFAULT to force application-level timestamp generation

#### 2. **server.py** (Ensure Explicit Timestamps)
**Location:** `create_task()` function (~line 130)

**BEFORE:**
```python
cursor.execute(
    """
    INSERT INTO tasks (
        title, description, status, priority, parent_task_id,
        depends_on, tags, blocker_reason, file_references, created_by
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
    (
        task_data.title,
        task_data.description,
        # ... other fields
    ),
)
```

**AFTER:**
```python
from datetime import datetime

now = datetime.now().isoformat()

cursor.execute(
    """
    INSERT INTO tasks (
        title, description, status, priority, parent_task_id,
        depends_on, tags, blocker_reason, file_references, created_by,
        created_at, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
    (
        task_data.title,
        task_data.description,
        # ... other fields
        now,  # created_at
        now,  # updated_at
    ),
)
```

**Rationale:** Explicitly set both timestamps at creation time

#### 3. **models.py** (Consistency Fix - Optional)
**Location:** Line 307

**BEFORE:**
```python
self.completed_at = datetime.utcnow()
```

**AFTER:**
```python
self.completed_at = datetime.utcnow().isoformat()
```

**Note:** This is defensive. In practice, `server.py` sets `completed_at` explicitly, so this model validator rarely executes.

---

## Migration Strategy

### Database Compatibility
**Good News:** No migration needed!

**Why?**
- Existing timestamps in both formats parse correctly as Python `datetime` objects
- Pydantic's `strict=False` configuration allows coercion
- Both formats are valid SQLite TIMESTAMP values
- Queries using `<`, `>`, `BETWEEN` work correctly (lexicographic ordering)

**Backward Compatibility:**
- Existing records with space-separated timestamps remain valid
- New records will use ISO 8601 'T' separator
- Both formats sort correctly in SQLite queries
- Pydantic models accept both formats on read

### Testing Strategy
1. Create new task → verify ISO 8601 format
2. Update existing task → verify ISO 8601 format
3. Query tasks with mixed formats → verify correct parsing
4. Sort by timestamp → verify correct ordering

---

## Summary of Changed Locations

### Files to Modify
1. **`src/task_mcp/database.py`**: Remove DEFAULT CURRENT_TIMESTAMP from schema (lines 92-93)
2. **`src/task_mcp/server.py`**: Add explicit timestamp parameters to INSERT statement in `create_task()` (~line 130)

### Timestamp Fields Affected
| Field | Current Source | New Source | Format |
|-------|----------------|------------|--------|
| `created_at` | SQLite DEFAULT | Python explicit | `datetime.now().isoformat()` |
| `updated_at` | SQLite DEFAULT (create) / Python (update) | Python explicit | `datetime.now().isoformat()` |
| `completed_at` | Python explicit | Python explicit | Already correct ✓ |
| `deleted_at` | Python explicit | Python explicit | Already correct ✓ |

---

## Expected Outcome

**After Implementation:**
- **All timestamp fields** will consistently use ISO 8601 format: `2025-10-27T15:30:28.123456`
- **API responses** will have uniform timestamp representation
- **Developer experience** improved with consistent date parsing
- **No breaking changes** - both formats remain parseable
- **Full backward compatibility** with existing database records

---

## Risk Assessment

**Risk Level:** LOW

**Justification:**
- No data migration required
- Backward compatible with existing records
- Pydantic validation accepts both formats
- SQLite timestamp comparison works with both formats
- All explicit timestamp operations already use `.isoformat()`

---

## Next Steps

1. ✅ Analysis complete (this document)
2. ⏳ Implement schema changes in `database.py`
3. ⏳ Add explicit timestamps to `create_task()` in `server.py`
4. ⏳ Run test suite to verify no regressions
5. ⏳ Create micro-commit: "fix(database): standardize all timestamps to ISO 8601 format"

---

**Report Generated:** 2025-10-27 15:30 UTC
**Author:** python-wizard (Claude Code Agent)
**Confidence Level:** HIGH
