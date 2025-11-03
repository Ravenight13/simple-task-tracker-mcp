# Entity Viewer - End-to-End Test Scenarios

**Document Version:** 1.0
**Last Updated:** 2025-11-02
**Purpose:** Comprehensive E2E testing scenarios for Entity Viewer feature

---

## Overview

This document outlines complete end-to-end workflow scenarios for testing the Entity Viewer feature in the Task Viewer application. Each scenario represents a typical user journey with detailed steps, expected results, and success criteria.

**Test Coverage:**
- Entity browsing and detail viewing
- Search functionality with debouncing
- Multi-filter operations (type + tags)
- Statistics display and updates

---

## Test Data Setup

Before running E2E tests, populate the workspace with test entities using the task-mcp MCP tools.

### Required Test Data

**1. File Entities (5 entities):**
```python
# Entity 1: Python backend file
create_entity(
    entity_type="file",
    name="Authentication Controller",
    identifier="/src/api/auth.py",
    description="Handles user login, logout, and session management",
    metadata='{"language": "python", "line_count": 250, "last_modified": "2025-10-30"}',
    tags="backend api authentication python",
    workspace_path="/path/to/workspace"
)

# Entity 2: React frontend component
create_entity(
    entity_type="file",
    name="Login Component",
    identifier="/src/components/Login.tsx",
    description="User login form with validation",
    metadata='{"language": "typescript", "framework": "react", "line_count": 120}',
    tags="frontend ui react typescript authentication",
    workspace_path="/path/to/workspace"
)

# Entity 3: Database schema
create_entity(
    entity_type="file",
    name="User Schema",
    identifier="/database/schemas/users.sql",
    description="User table schema with indexes",
    metadata='{"database": "postgresql", "tables": ["users", "sessions"]}',
    tags="database schema sql",
    workspace_path="/path/to/workspace"
)

# Entity 4: API documentation
create_entity(
    entity_type="file",
    name="API Documentation",
    identifier="/docs/api/authentication.md",
    description="Authentication API endpoints documentation",
    metadata='{"format": "markdown", "endpoints": 5}',
    tags="documentation api",
    workspace_path="/path/to/workspace"
)

# Entity 5: Config file
create_entity(
    entity_type="file",
    name="Auth Config",
    identifier="/config/auth.yaml",
    description="Authentication service configuration",
    metadata='{"format": "yaml", "environment": "production"}',
    tags="config authentication",
    workspace_path="/path/to/workspace"
)
```

**2. Other Entities (3 entities):**
```python
# Entity 6: Vendor
create_entity(
    entity_type="other",
    name="ABC Insurance",
    identifier="ABC-INS",
    description="Primary insurance vendor for health plans",
    metadata='{"vendor_code": "ABC-INS", "phase": "active", "formats": ["xlsx", "pdf"], "brands": ["Brand A", "Brand B"]}',
    tags="vendor insurance active",
    workspace_path="/path/to/workspace"
)

# Entity 7: Team member
create_entity(
    entity_type="other",
    name="Jane Smith",
    identifier="jsmith",
    description="Senior backend engineer - authentication specialist",
    metadata='{"role": "engineer", "team": "backend", "specialty": "auth"}',
    tags="team backend",
    workspace_path="/path/to/workspace"
)

# Entity 8: External API
create_entity(
    entity_type="other",
    name="Stripe Payment API",
    identifier="stripe-v2",
    description="Payment processing API integration",
    metadata='{"api_version": "2023-10-16", "status": "active"}',
    tags="api payment integration",
    workspace_path="/path/to/workspace"
)
```

**3. Create Tasks and Links:**
```python
# Create sample task
task = create_task(
    title="Implement OAuth2 authentication",
    description="Add OAuth2 support to authentication system",
    status="in_progress",
    priority="high",
    tags="authentication backend",
    workspace_path="/path/to/workspace"
)

# Link entities to task
link_entity_to_task(task_id=task["id"], entity_id=1, workspace_path="/path/to/workspace")  # Auth Controller
link_entity_to_task(task_id=task["id"], entity_id=2, workspace_path="/path/to/workspace")  # Login Component
link_entity_to_task(task_id=task["id"], entity_id=6, workspace_path="/path/to/workspace")  # ABC Insurance
```

**Expected Data Summary:**
- Total entities: 8 (5 file + 3 other)
- Total tags: 14 unique tags
- Linked entities: 3 (to 1 task)
- Unlinked entities: 5

---

## Scenario 1: Browse and View Entity

**Scenario ID:** E2E-ENTITY-001
**Priority:** High
**Estimated Duration:** 2-3 minutes

### Prerequisites
- Task Viewer application running at http://localhost:5174
- Test data populated (8 entities as defined above)
- At least 1 entity linked to a task

### Test Steps

| Step | Action | Expected Result |
|------|--------|----------------|
| 1.1 | Open browser and navigate to http://localhost:5174 | Task Viewer loads, displays Tasks tab by default |
| 1.2 | Click "Entities" tab in tab bar | Tab switches to Entities view |
| 1.3 | Observe entity list | 8 entity cards displayed in grid layout |
| 1.4 | Verify entity card content | Each card shows: name, identifier (truncated), type badge (blue "FILE" or green "OTHER"), tag chips |
| 1.5 | Identify entity with linked tasks | Card shows "Linked to N tasks" text |
| 1.6 | Click entity card (e.g., "Authentication Controller") | Entity detail modal opens with overlay |
| 1.7 | Verify modal header | Shows entity name, type badge, and close button (X) |
| 1.8 | Verify modal sections | Shows: Details, Metadata (if present), Tags, Linked Tasks |
| 1.9 | Read entity details | Identifier displayed as clickable code block, description shown in full |
| 1.10 | Expand Metadata section | JSON metadata displayed with syntax highlighting |
| 1.11 | Observe Tags section | All tags displayed as colored chips |
| 1.12 | Scroll to Linked Tasks section | Shows list of linked tasks with task IDs, titles, status badges, priority labels |
| 1.13 | Click linked task title | Task detail modal opens (replaces entity modal) |
| 1.14 | Close task detail modal | Returns to entity detail modal |
| 1.15 | Click X button or overlay | Entity detail modal closes, returns to entity list |

### Success Criteria
- All entity cards render correctly with proper styling
- Type badges use correct colors (blue/green)
- Modal opens/closes smoothly without errors
- All entity data fields display correctly
- Linked tasks section shows accurate task information
- Navigation between entity and task modals works seamlessly
- No console errors during workflow

### Edge Cases to Test
- Entity with no identifier (should show "N/A")
- Entity with no metadata (section should be hidden or show "No metadata")
- Entity with no tags (section should show "No tags")
- Entity with no linked tasks (section should show "No linked tasks")
- Very long entity names (should truncate with ellipsis)
- Very long identifiers (should truncate in card, show full in modal)

---

## Scenario 2: Search for Entity

**Scenario ID:** E2E-ENTITY-002
**Priority:** High
**Estimated Duration:** 2-3 minutes

### Prerequisites
- Task Viewer application running
- Test data populated (8 entities)
- User on Entities tab

### Test Steps

| Step | Action | Expected Result |
|------|--------|----------------|
| 2.1 | Navigate to Entities tab | 8 entities displayed |
| 2.2 | Observe search bar | Search input visible with placeholder "Search entities by name or identifier..." |
| 2.3 | Type "auth" in search bar | After 300ms debounce, results filter to show entities containing "auth" |
| 2.4 | Verify search results | Shows: "Authentication Controller", "Auth Config" (2 results) |
| 2.5 | Observe result count | Statistics panel updates to show "Total: 2" |
| 2.6 | Type additional characters "authe" | Results update to show only "Authentication Controller" (1 result) |
| 2.7 | Clear search input (backspace all) | After 300ms, all 8 entities re-appear |
| 2.8 | Type "ABC" in search bar | Results filter to "ABC Insurance" (1 result) |
| 2.9 | Type identifier fragment "/src/api" | Results filter to "Authentication Controller" (matches identifier) |
| 2.10 | Type non-existent term "xyz123" | Results show "No entities found" message |
| 2.11 | Click X button in search input | Search clears, all 8 entities re-appear |

### Success Criteria
- Search debouncing works (300ms delay, no premature filtering)
- Search matches both name AND identifier fields
- Search is case-insensitive
- Result count updates accurately
- Statistics panel reflects filtered results
- Clear button (X) appears when search has text
- "No entities found" message displays for empty results
- No console errors during search operations

### Performance Expectations
- Search results appear within 50ms after debounce
- UI remains responsive during typing
- No visible lag or flicker during result updates

### Edge Cases to Test
- Search with special characters (!@#$%^&*)
- Search with very long query string (100+ characters)
- Rapid typing (verify debounce cancels previous searches)
- Search while filters active (should combine search + filters)

---

## Scenario 3: Filter Entities by Type and Tag

**Scenario ID:** E2E-ENTITY-003
**Priority:** High
**Estimated Duration:** 3-4 minutes

### Prerequisites
- Task Viewer application running
- Test data populated (8 entities: 5 file + 3 other)
- User on Entities tab

### Test Steps

| Step | Action | Expected Result |
|------|--------|----------------|
| 3.1 | Navigate to Entities tab | 8 entities displayed, no filters active |
| 3.2 | Observe filter controls | Type dropdown (All Types) and Tag dropdown (All Tags) visible |
| 3.3 | Click Type dropdown | Dropdown opens showing: All Types, File, Other |
| 3.4 | Select "File" option | Dropdown closes, filter chip appears "Type: file" |
| 3.5 | Verify filtered results | 5 entities displayed (all file type) |
| 3.6 | Verify statistics update | Total count shows 5, type breakdown shows 100% File |
| 3.7 | Click Tag dropdown | Dropdown opens showing all available tags with counts |
| 3.8 | Select "authentication" tag | Tag filter chip appears "Tag: authentication" |
| 3.9 | Verify double-filtered results | Shows entities that are file type AND have authentication tag (2 entities expected) |
| 3.10 | Verify statistics update | Total count shows 2, stats reflect filtered subset |
| 3.11 | Click X on "Type: file" chip | Type filter removed, shows 3 entities with authentication tag (any type) |
| 3.12 | Verify results update | More entities appear (includes non-file types with authentication tag) |
| 3.13 | Add Type filter again (Other) | Results show only "other" type entities with authentication tag (0-1 results) |
| 3.14 | Click "Clear Filters" button | All filters removed, all 8 entities reappear |
| 3.15 | Apply multiple tag filters | Select "backend" tag, then add "api" tag |
| 3.16 | Verify multi-tag filtering | Shows entities with BOTH backend AND api tags (intersection logic) |

### Success Criteria
- Type filter works correctly (File/Other/All)
- Tag filter works correctly (individual tags)
- Filter chips display accurately
- Remove chip (X button) removes that specific filter
- Clear Filters button removes all filters
- Statistics panel updates with each filter change
- Multiple filters work together (AND logic)
- No console errors during filter operations

### Filter Logic Verification
- Type filter: Exact match on entity_type field
- Tag filter: Substring match on tags field
- Combined filters: Results must match ALL active filters (AND logic, not OR)

### Edge Cases to Test
- Apply filter with no matching results (shows "No entities found")
- Remove filters in different order than applied
- Apply same filter twice (should not create duplicate chips)
- Rapidly toggle filters (verify state consistency)
- Filter while search is active (verify combined filtering)

---

## Scenario 4: View Entity Statistics

**Scenario ID:** E2E-ENTITY-004
**Priority:** Medium
**Estimated Duration:** 2-3 minutes

### Prerequisites
- Task Viewer application running
- Test data populated (8 entities: 5 file + 3 other)
- User on Entities tab

### Test Steps

| Step | Action | Expected Result |
|------|--------|----------------|
| 4.1 | Navigate to Entities tab | Statistics panel visible at top of page |
| 4.2 | Locate Total Count | Shows "Total: 8" |
| 4.3 | Locate Type Breakdown section | Shows "File: 5 (62.5%)" and "Other: 3 (37.5%)" |
| 4.4 | Verify percentage calculation | 5/8 = 62.5%, 3/8 = 37.5% (correct) |
| 4.5 | Locate Top Tags section | Shows list of most common tags with counts |
| 4.6 | Verify tag counts | "authentication: 3", "backend: 2", "api: 2", etc. (verify against test data) |
| 4.7 | Apply Type filter (File) | Statistics update instantly |
| 4.8 | Verify updated stats | Total: 5, Type breakdown: File 100%, Other 0% |
| 4.9 | Verify updated top tags | Only shows tags from file entities |
| 4.10 | Add Tag filter (authentication) | Statistics update to reflect double filter |
| 4.11 | Verify stats accuracy | Total shows count of file entities with authentication tag |
| 4.12 | Clear all filters | Statistics return to original values (Total: 8, original breakdown) |
| 4.13 | Use search to filter | Type "auth" in search bar |
| 4.14 | Verify search affects stats | Statistics reflect only searched results |
| 4.15 | Test empty result set | Apply filter with no matches, verify stats show Total: 0 |

### Success Criteria
- Total count displays correctly
- Type breakdown shows accurate counts and percentages
- Percentages sum to 100% (or close due to rounding)
- Top tags show accurate counts
- Statistics update in real-time with filters
- Statistics update with search results
- Zero state handled correctly (Total: 0 when no results)
- No console errors during statistics updates

### Calculation Verification
- Total count = number of visible entities (after filters)
- Type percentages = (type_count / total_count) * 100
- Tag counts = number of entities with that tag (in filtered set)
- Top tags sorted by count descending

### Edge Cases to Test
- Filter to single entity (100% in one category)
- Filter to empty result set (0% in all categories)
- Very large tag counts (verify formatting)
- Tag ties (same count, verify consistent sorting)

---

## Scenario 5: Pagination and Scrolling

**Scenario ID:** E2E-ENTITY-005
**Priority:** Medium
**Estimated Duration:** 2 minutes

### Prerequisites
- Task Viewer application running
- Test data populated (8 entities)
- User on Entities tab

### Test Steps

| Step | Action | Expected Result |
|------|--------|----------------|
| 5.1 | Navigate to Entities tab | All entities visible (8 < 20 per page default) |
| 5.2 | Scroll down page | Page scrolls smoothly |
| 5.3 | Scroll back up | Page scrolls smoothly |
| 5.4 | Observe pagination controls | If entities < 20, pagination controls not visible OR showing "Page 1 of 1" |

### Success Criteria
- Smooth scrolling behavior
- No layout shift during scroll
- Pagination controls appear only when needed
- Entity grid maintains consistent layout

### Notes
- With 8 test entities, pagination will not be active (threshold = 20)
- To fully test pagination, create 25+ test entities
- Future testing should verify page navigation, items per page selector

---

## Cross-Cutting Concerns

### Responsive Design
- Test all scenarios on desktop (1920x1080)
- Test on tablet viewport (768x1024)
- Test on mobile viewport (375x667)
- Verify grid layout adjusts (cards stack on mobile)
- Verify modal is scrollable on small screens

### Performance Benchmarks
- Entity list renders in < 200ms with 8 entities
- Search debounce delay: 300ms
- Filter application: < 50ms
- Modal open/close animation: < 300ms
- No memory leaks after 10+ modal open/close cycles

### Accessibility
- Tab navigation works through all interactive elements
- Enter key opens entity detail modal
- Escape key closes modal
- Screen reader announces entity count changes
- Focus trap in modal (focus stays within modal when open)

### Error Handling
- Network error when fetching entities (shows error message)
- Invalid entity data (gracefully handles missing fields)
- Failed search operation (shows error toast, maintains previous results)

---

## Test Execution Checklist

Use this checklist when executing E2E tests:

- [ ] Test data created (8 entities as specified)
- [ ] Task Viewer running on http://localhost:5174
- [ ] Browser console open (monitoring for errors)
- [ ] Network tab open (monitoring API calls)
- [ ] Scenario 1 (Browse and View) - PASS/FAIL
- [ ] Scenario 2 (Search) - PASS/FAIL
- [ ] Scenario 3 (Filter) - PASS/FAIL
- [ ] Scenario 4 (Statistics) - PASS/FAIL
- [ ] Scenario 5 (Pagination) - PASS/FAIL
- [ ] Edge cases tested - PASS/FAIL
- [ ] No console errors - PASS/FAIL
- [ ] Performance benchmarks met - PASS/FAIL

---

## Bug Report Template

When issues are found during E2E testing, use this template:

```
**Bug ID:** ENTITY-BUG-XXX
**Scenario:** [Scenario ID]
**Severity:** Critical / High / Medium / Low
**Step:** [Step number where issue occurred]

**Expected Behavior:**
[What should happen]

**Actual Behavior:**
[What actually happened]

**Reproduction Steps:**
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Environment:**
- Browser: [Chrome/Firefox/Safari version]
- OS: [Windows/Mac/Linux]
- Task Viewer version: [version]

**Console Errors:**
[Any errors from browser console]

**Screenshots:**
[Attach screenshots if applicable]
```

---

## Future Test Scenarios

Additional scenarios to implement in future iterations:

1. **Entity Creation via UI** (when create entity form added)
2. **Entity Editing via UI** (when edit functionality added)
3. **Entity Deletion** (when delete functionality added)
4. **Bulk Operations** (select multiple, bulk link/unlink)
5. **Entity Export** (export entity list to CSV/JSON)
6. **Keyboard Shortcuts** (navigate entities with arrow keys)
7. **Advanced Filtering** (date ranges, metadata queries)
8. **Entity Comparison** (compare two entities side-by-side)

---

## Document Maintenance

**Review Schedule:** Quarterly or after major feature releases

**Update Triggers:**
- New entity viewer features added
- UI changes that affect user workflows
- Bug fixes that change expected behavior
- Performance optimization changes

**Owner:** QA Team / Testing Lead

---

**End of Document**
