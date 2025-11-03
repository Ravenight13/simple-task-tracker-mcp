# Entity Pagination Implementation Guide (Task #124)

## Status
**BLOCKED** - Waiting for Task #116 (Entity Cards) to be completed

## Overview
This document outlines the implementation of entity pagination for the task-viewer UI. The pagination system is designed to handle large entity lists efficiently with page size selection, page navigation, and smooth UX.

## Current Progress

### ✅ Completed: Pagination State Variables
Already added to `task-viewer/static/index.html` (lines ~1329-1332):

```javascript
// Entity Pagination State
entityCurrentPage: 1,
entityTotalEntities: 0,
entityTotalPages: 1,
```

### ✅ Completed: Entity Filters with Pagination Support
Already exists (lines ~1320-1326):

```javascript
entityFilters: {
  type: '',      // '' | 'file' | 'other'
  tags: [],      // array of selected tag strings
  limit: 25,     // Page size
  offset: 0      // Current offset
},
```

### ✅ Completed: loadEntities Method
Already implemented with pagination support (lines ~1410-1450). It:
- Uses `entityFilters.limit` and `entityFilters.offset`
- Calculates `entityTotalPages` from response
- Updates `entityTotalEntities` from API response
- Handles loading state with `entitiesLoading`

## Remaining Implementation

### 1. Add Pagination Methods (JavaScript)

Add these methods after `clearEntitySearch()` (around line 1542):

```javascript
// Entity pagination computed properties
get entityPaginationStart() {
  return this.entityTotalEntities === 0 ? 0 : (this.entityCurrentPage - 1) * this.entityFilters.limit + 1;
},

get entityPaginationEnd() {
  return Math.min(this.entityCurrentPage * this.entityFilters.limit, this.entityTotalEntities);
},

get entityVisiblePages() {
  const pages = [];
  const total = this.entityTotalPages;
  const current = this.entityCurrentPage;

  // Show max 5 pages centered around current
  let start = Math.max(1, current - 2);
  let end = Math.min(total, start + 4);

  if (end - start < 4) {
    start = Math.max(1, end - 4);
  }

  for (let i = start; i <= end; i++) {
    pages.push(i);
  }

  return pages;
},

// Entity pagination navigation methods
entityPreviousPage() {
  if (this.entityCurrentPage > 1) {
    this.entityCurrentPage--;
    this.loadEntitiesPage();
  }
},

entityNextPage() {
  if (this.entityCurrentPage < this.entityTotalPages) {
    this.entityCurrentPage++;
    this.loadEntitiesPage();
  }
},

entityGoToPage(page) {
  this.entityCurrentPage = page;
  this.loadEntitiesPage();
},

changeEntityPageSize() {
  this.entityCurrentPage: 1; // Reset to first page
  this.loadEntitiesPage();
},

loadEntitiesPage() {
  this.entityFilters.offset = (this.entityCurrentPage - 1) * this.entityFilters.limit;
  this.loadEntities();

  // Scroll to top of entity list
  const container = document.getElementById('entities-container');
  if (container) {
    container.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
},
```

### 2. Add Pagination UI Controls (HTML)

Add this pagination control section **after** the entity cards grid (once Task #116 is complete):

**Location**: Inside the entities tab, after the entity cards loop, before the closing `</div>` of the entities view.

```html
<!-- Entity Pagination Controls -->
<div
  x-show="entities.length > 0 && entityTotalPages > 1"
  id="entity-pagination"
  class="flex flex-col sm:flex-row justify-between items-center gap-4 mt-6 p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700"
>
  <!-- Results summary -->
  <p class="text-sm text-gray-600 dark:text-gray-400">
    Showing
    <span class="font-semibold" x-text="entityPaginationStart"></span>-<span class="font-semibold" x-text="entityPaginationEnd"></span>
    of
    <span class="font-semibold" x-text="entityTotalEntities"></span>
    entities
  </p>

  <!-- Page navigation -->
  <div class="flex items-center gap-2">
    <button
      @click="entityPreviousPage()"
      :disabled="entityCurrentPage === 1"
      :class="entityCurrentPage === 1 ? 'opacity-50 cursor-not-allowed' : 'hover:bg-gray-100 dark:hover:bg-gray-700'"
      class="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded text-sm font-medium text-gray-700 dark:text-gray-300 transition-colors"
      aria-label="Previous page"
    >
      Previous
    </button>

    <!-- Page numbers (show max 5) -->
    <template x-for="page in entityVisiblePages" :key="page">
      <button
        @click="entityGoToPage(page)"
        :class="entityCurrentPage === page ? 'bg-blue-500 text-white border-blue-500' : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 border-gray-300 dark:border-gray-600'"
        class="px-3 py-1 border rounded text-sm font-medium transition-colors"
        :aria-label="'Go to page ' + page"
        :aria-current="entityCurrentPage === page ? 'page' : undefined"
        x-text="page"
      >
      </button>
    </template>

    <button
      @click="entityNextPage()"
      :disabled="entityCurrentPage >= entityTotalPages"
      :class="entityCurrentPage >= entityTotalPages ? 'opacity-50 cursor-not-allowed' : 'hover:bg-gray-100 dark:hover:bg-gray-700'"
      class="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded text-sm font-medium text-gray-700 dark:text-gray-300 transition-colors"
      aria-label="Next page"
    >
      Next
    </button>
  </div>

  <!-- Page size selector -->
  <div class="flex items-center gap-2">
    <label for="entity-page-size" class="text-sm text-gray-600 dark:text-gray-400">Per page:</label>
    <select
      id="entity-page-size"
      x-model.number="entityFilters.limit"
      @change="changeEntityPageSize()"
      class="border border-gray-300 dark:border-gray-600 rounded px-2 py-1 text-sm bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
    >
      <option value="25">25</option>
      <option value="50">50</option>
      <option value="100">100</option>
    </select>
  </div>
</div>
```

### 3. Update Entity Cards Container

Ensure the entity cards container has the ID for scroll targeting:

```html
<div id="entities-container" class="space-y-4">
  <!-- Entity cards will be rendered here by Task #116 -->
  <template x-for="entity in entities" :key="entity.id">
    <!-- Entity card component -->
  </template>
</div>
```

### 4. Integration with Existing Filters

The pagination already integrates with filters via `selectEntityTag` and `selectEntityType` methods (lines ~1463-1487):

```javascript
selectEntityTag(tag) {
  this.selectedEntityTag = tag;
  this.entityFilters.offset = 0;
  this.entityCurrentPage = 1;  // Reset to first page
  this.loadEntities();
},

selectEntityType(type) {
  this.entityFilters.type = type;
  this.entityFilters.offset = 0;
  this.entityCurrentPage = 1;  // Reset to first page
  this.loadEntities();
},
```

## Acceptance Criteria Checklist

Once implemented, verify:

- [ ] **Pagination controls visible**: Previous, Next, and page numbers display when entities > page size
- [ ] **Page size selector works**: Can switch between 25, 50, 100 items per page
- [ ] **Results summary displays**: Shows "Showing X-Y of Z entities" with correct values
- [ ] **Page navigation works**: Can click Previous, Next, and specific page numbers
- [ ] **Boundary states correct**: Previous disabled on page 1, Next disabled on last page
- [ ] **Smooth scroll**: Clicking navigation scrolls to top of entity list
- [ ] **Filter integration**: Changing filters resets to page 1
- [ ] **Responsive layout**: Pagination controls stack vertically on mobile
- [ ] **Accessibility**: All buttons have aria-labels, current page marked with aria-current
- [ ] **Dark mode support**: Pagination controls properly styled for dark mode

## Testing Steps

1. **Load entities**: Navigate to Entities tab
2. **Verify initial state**: Should show page 1 with default 25 items
3. **Test page size**: Change to 50/100 and verify entity count updates
4. **Test navigation**: Click Next/Previous and verify entities update
5. **Test page numbers**: Click specific page and verify correct entities load
6. **Test boundaries**: Verify disabled states at first/last pages
7. **Test filters**: Apply entity type/tag filter, verify reset to page 1
8. **Test scroll**: Navigate pages and verify smooth scroll to top
9. **Test responsive**: Resize window, verify controls stack properly
10. **Test dark mode**: Toggle dark mode, verify styles render correctly

## API Requirements

The existing `/api/entities` endpoint must return:

```json
{
  "entities": [...],
  "total": 150,  // Total count for pagination
  "limit": 25,
  "offset": 0
}
```

This is already implemented in the backend.

## Notes

- Pagination state is preserved when switching between entity type/tag filters
- Page size preference could be stored in localStorage (future enhancement)
- URL query params for pagination state (mentioned in acceptance criteria) is deferred to future task
- The `entityVisiblePages` getter ensures max 5 page numbers show at once for clean UI

## Dependencies

- **Blocks**: None (this is the final entity viewer task)
- **Blocked by**: Task #116 (Entity Cards) - MUST BE COMPLETED FIRST

## Estimated Time

**1.5 hours total**:
- 30 min: Add JavaScript methods
- 45 min: Implement pagination UI with proper styling
- 15 min: Testing and refinement
