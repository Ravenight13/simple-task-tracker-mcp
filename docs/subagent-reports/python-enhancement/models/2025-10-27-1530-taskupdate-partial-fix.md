# TaskUpdate Partial Validation Fix Analysis

**Date:** 2025-10-27 15:30
**Agent:** python-wizard
**Enhancement:** v0.2.0 #3 - TaskUpdate Model Partial Updates

## Problem Statement

The TaskUpdate model currently requires workarounds for partial updates because field validators don't handle None values gracefully. When updating only specific fields, the validators run on None values for unchanged fields, causing validation errors.

**Current Behavior:**
```python
# Fails because status validator runs on None
task_update = TaskUpdate(title="New Title")  # ValidationError

# Workaround: must pass all current values
task_update = TaskUpdate(title="New Title", status="todo", priority="medium")
```

**Expected Behavior:**
```python
# Should work - only validate non-None fields
task_update = TaskUpdate(title="New Title")  # Success
```

## Root Cause Analysis

### File: `src/task_mcp/models.py`

**Lines 426-438: TaskUpdate Field Validators**

The TaskUpdate model reuses validators from the Task model using this pattern:
```python
_validate_status = field_validator('status')(
    Task.validate_status.__func__  # type: ignore[attr-defined]
)
```

**Problematic Validators:**

1. **Line 430-432: `_validate_status`**
   - Inherited from Task.validate_status (line 254-262)
   - Expects `v: str` parameter
   - Does NOT check for None before validation
   - Fails on None input for partial updates

2. **Line 433-435: `_validate_priority`**
   - Inherited from Task.validate_priority (line 264-272)
   - Expects `v: str` parameter
   - Does NOT check for None before validation
   - Fails on None input for partial updates

3. **Line 427-429: `_validate_description`** (edge case)
   - Inherited from Task.validate_description_length (line 243-252)
   - Already has None check at line 247: `if v is not None`
   - Works correctly but should be consistent with fix pattern

**Working Validator:**

4. **Line 436-438: `_validate_tags`**
   - Inherited from Task.validate_and_normalize_tags (line 274-280)
   - HAS None check at line 278: `if v is None: return None`
   - Works correctly for partial updates ✓

## Solution Design

### Strategy: Early Return Pattern

Update validators to return early if value is None (before validation logic):

```python
@field_validator('status')
@classmethod
def validate_status(cls, v: Optional[str]) -> Optional[str]:
    """Validate status is one of the allowed values."""
    if v is None:  # ADD THIS CHECK
        return None
    if v not in VALID_STATUSES:
        raise ValueError(...)
    return v
```

### Changes Required

**File: `src/task_mcp/models.py`**

1. **Task.validate_status (line 254-262)**
   - Change parameter type: `v: str` → `v: Optional[str]`
   - Change return type: `str` → `Optional[str]`
   - Add None check as first line: `if v is None: return None`

2. **Task.validate_priority (line 264-272)**
   - Change parameter type: `v: str` → `v: Optional[str]`
   - Change return type: `str` → `Optional[str]`
   - Add None check as first line: `if v is None: return None`

### Type Safety Considerations

**Pydantic v2 Validator Behavior:**
- Field validators run BEFORE field assignment
- For `Optional[str]` fields, validator receives None when field not provided
- Validators must handle None gracefully to support optional fields
- Return type must match field type (including Optional)

**Backward Compatibility:**
- More permissive (not restrictive) - no breaking changes
- Task model still enforces defaults ("todo", "medium") via Field(default=...)
- TaskCreate inherits same validators - gains flexibility for optional status/priority
- TaskUpdate becomes fully functional for partial updates

## Testing Strategy

### Test Cases to Verify

1. **Partial Update - Title Only**
   ```python
   update = TaskUpdate(title="New Title")
   assert update.title == "New Title"
   assert update.status is None
   assert update.priority is None
   ```

2. **Partial Update - Status Only**
   ```python
   update = TaskUpdate(status="in_progress")
   assert update.status == "in_progress"
   assert update.title is None
   ```

3. **Partial Update - Priority Only**
   ```python
   update = TaskUpdate(priority="high")
   assert update.priority == "high"
   ```

4. **Full Update - All Fields**
   ```python
   update = TaskUpdate(
       title="Title",
       status="in_progress",
       priority="high"
   )
   # All validations still run
   ```

5. **Invalid Values Still Rejected**
   ```python
   # Should raise ValidationError
   update = TaskUpdate(status="invalid")
   ```

### Regression Testing

Ensure existing behavior unchanged:
- Task model still validates with defaults
- TaskCreate still validates required fields
- Invalid values still raise ValidationError
- Tags still normalize correctly

## Implementation Checklist

- [x] Analyze current implementation
- [x] Identify problematic validators
- [x] Design solution with type safety
- [ ] Update Task.validate_status method
- [ ] Update Task.validate_priority method
- [ ] Run mypy --strict validation
- [ ] Run pytest to verify no regressions
- [ ] Micro-commit changes

## Expected Outcomes

### Before Fix
```python
# Fails with ValidationError
TaskUpdate(title="New Title")
```

### After Fix
```python
# Works - validates only provided fields
TaskUpdate(title="New Title")  # ✓
TaskUpdate(status="in_progress")  # ✓
TaskUpdate(priority="high")  # ✓
TaskUpdate(title="Title", status="in_progress", priority="high")  # ✓

# Still rejects invalid values
TaskUpdate(status="invalid")  # ValidationError ✓
TaskUpdate(priority="extreme")  # ValidationError ✓
```

## Pydantic v2 Best Practices Applied

1. **Type Annotations:** Use `Optional[str]` for validators that accept None
2. **Early Returns:** Return None immediately for None inputs
3. **Consistent Patterns:** All validators follow same None-handling pattern
4. **No Side Effects:** Validators don't modify external state
5. **Clear Error Messages:** Validation errors remain descriptive

## Notes

- The `_validate_tags` validator already handles None correctly (good reference)
- The `_validate_description` validator has None check but inconsistent type signature
- BeforeValidator functions (validate_json_list_of_ints, validate_json_list_of_strings) already handle None correctly
- Model validator `validate_blocker_reason_if_blocked` correctly only validates when status='blocked'

## References

- Pydantic v2 docs: https://docs.pydantic.dev/latest/concepts/validators/
- FastMCP patterns: https://github.com/jlowin/fastmcp
- Project standards: `/docs/standards/constitutional-compliance.md`
