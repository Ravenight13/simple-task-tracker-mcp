# Entity Viewer UI Testing Checklist

**Version:** 1.0
**Date:** 2025-11-02
**Task:** #126 - UI Component Testing
**Tester:** _________________
**Test Date:** _________________

## Overview

This checklist provides comprehensive manual testing procedures for all Entity Viewer UI components. Each test case includes a unique ID, description, steps to test, and expected results.

**Testing Environment:**
- Task Viewer running locally
- Browser: _________________
- Screen Resolution: _________________
- OS: _________________

**Pass Criteria:** All checkboxes marked ✓ with no critical issues

---

## 1. Entities Tab Navigation

### TEST-NAV-001: Tab Visibility
- [ ] **PASS** / [ ] **FAIL**

**Description:** Verify entities tab appears in main navigation
**Steps:**
1. Open task-viewer in browser
2. Locate navigation tabs at top of page

**Expected Result:**
- "Entities" tab visible alongside "Tasks" tab
- Tab label clearly readable
- Tab styling consistent with Tasks tab

**Notes:**
_______________________________________________________________

---

### TEST-NAV-002: Tab Switching
- [ ] **PASS** / [ ] **FAIL**

**Description:** Verify clicking entities tab switches view
**Steps:**
1. Start on Tasks tab
2. Click "Entities" tab
3. Click back to "Tasks" tab
4. Return to "Entities" tab

**Expected Result:**
- Clicking Entities tab displays entities content
- Tasks content hidden when on Entities tab
- Tab has active state indicator (underline/highlight)
- Smooth transition between tabs
- No console errors

**Notes:**
_______________________________________________________________

---

### TEST-NAV-003: Count Badge Display
- [ ] **PASS** / [ ] **FAIL**

**Description:** Verify entity count badge displays correctly
**Steps:**
1. Check Entities tab for count badge
2. Note displayed count
3. Verify count matches actual entities shown

**Expected Result:**
- Badge shows total entity count (e.g., "42")
- Badge positioned to right of "Entities" label
- Badge styling consistent with Tasks badge
- Count accurate

**Notes:**
_______________________________________________________________

---

### TEST-NAV-004: URL Hash Routing
- [ ] **PASS** / [ ] **FAIL**

**Description:** Verify URL hash changes with tab selection
**Steps:**
1. Click Entities tab
2. Check browser URL for hash
3. Reload page with #entities hash
4. Click Tasks tab and verify hash change

**Expected Result:**
- URL changes to include #entities when tab clicked
- Direct navigation to URL with #entities loads Entities tab
- Browser back button switches between tabs correctly

**Notes:**
_______________________________________________________________

---

## 2. Entity Cards Display

### TEST-CARD-001: Card Rendering
- [ ] **PASS** / [ ] **FAIL**

**Description:** Verify entity cards render with all fields
**Steps:**
1. Navigate to Entities tab
2. Examine first 3 entity cards
3. Check each card displays all required fields

**Expected Result:**
Each card displays:
- Entity name (bold heading)
- Type badge ("file" or "other")
- Identifier (if present)
- Description snippet (truncated if long)
- Tags (if present)
- Creation date/time
- Linked tasks count

**Notes:**
_______________________________________________________________

---

### TEST-CARD-002: Type Badges
- [ ] **PASS** / [ ] **FAIL**

**Description:** Verify type badges show correct colors and icons
**Steps:**
1. Find card with entity_type = "file"
2. Find card with entity_type = "other"
3. Compare badge styling

**Expected Result:**
- File entities: Blue badge with file icon
- Other entities: Green badge with tag icon
- Badge text readable
- Icons clearly visible

**Notes:**
_______________________________________________________________

---

### TEST-CARD-003: Hover Effects
- [ ] **PASS** / [ ] **FAIL**

**Description:** Verify card hover states work correctly
**Steps:**
1. Hover mouse over entity card
2. Move mouse off card
3. Repeat on multiple cards

**Expected Result:**
- Card elevates/shadow increases on hover
- Border color changes (subtle highlight)
- Cursor changes to pointer
- Smooth transition animation
- No layout shift

**Notes:**
_______________________________________________________________

---

### TEST-CARD-004: Card Click Opens Modal
- [ ] **PASS** / [ ] **FAIL**

**Description:** Verify clicking card opens detail modal
**Steps:**
1. Click on entity card anywhere
2. Verify modal opens
3. Close modal and try another card

**Expected Result:**
- Modal opens on card click
- Modal displays correct entity details
- Background dims/blurs
- Body scroll locked while modal open

**Notes:**
_______________________________________________________________

---

### TEST-CARD-005: Empty State
- [ ] **PASS** / [ ] **FAIL**

**Description:** Verify empty state displays when no entities
**Steps:**
1. If entities exist, note this test requires clean database
2. Or apply filters that return zero results

**Expected Result:**
- "No entities found" message displayed
- Helpful text/icon shown
- Suggestion to create entities or adjust filters
- No broken layout

**Notes:**
_______________________________________________________________

---

## 3. Entity Detail Modal

### TEST-MODAL-001: Modal Open/Close
- [ ] **PASS** / [ ] **FAIL**

**Description:** Verify modal opens and closes correctly
**Steps:**
1. Click entity card to open modal
2. Click X button in top-right to close
3. Re-open modal, click backdrop to close
4. Re-open modal, press ESC key to close

**Expected Result:**
- Modal opens smoothly (fade-in animation)
- X button closes modal
- Clicking backdrop (outside modal) closes it
- ESC key closes modal
- Body scroll re-enabled after close

**Notes:**
_______________________________________________________________

---

### TEST-MODAL-002: Entity Fields Display
- [ ] **PASS** / [ ] **FAIL**

**Description:** Verify all entity fields display in modal
**Steps:**
1. Open modal for entity with complete data
2. Check each field section

**Expected Result:**
Modal displays:
- Entity name (header)
- Type badge
- Identifier (if present)
- Full description (not truncated)
- Tags (all tags visible)
- Created by conversation ID
- Created at timestamp
- Updated at timestamp
- Metadata section (if present)

**Notes:**
_______________________________________________________________

---

### TEST-MODAL-003: Metadata Viewer
- [ ] **PASS** / [ ] **FAIL**

**Description:** Verify metadata displays correctly as JSON
**Steps:**
1. Open entity with metadata field
2. Locate metadata section in modal
3. Check JSON formatting

**Expected Result:**
- Metadata displayed as formatted JSON
- Proper indentation
- Syntax highlighting (keys, values, brackets)
- Readable monospace font
- Scrollable if long

**Notes:**
_______________________________________________________________

---

### TEST-MODAL-004: Copy to Clipboard
- [ ] **PASS** / [ ] **FAIL**

**Description:** Verify copy button works for identifier
**Steps:**
1. Open entity with identifier
2. Click copy icon next to identifier
3. Paste into text editor to verify

**Expected Result:**
- Copy button visible next to identifier
- Clicking copies identifier to clipboard
- Visual feedback (checkmark or tooltip)
- Clipboard contains exact identifier text

**Notes:**
_______________________________________________________________

---

### TEST-MODAL-005: Linked Tasks Display
- [ ] **PASS** / [ ] **FAIL**

**Description:** Verify linked tasks section displays correctly
**Steps:**
1. Open entity with linked tasks
2. Check linked tasks section
3. Open entity with no linked tasks

**Expected Result:**
- Section titled "Linked Tasks" visible
- Each linked task shows: task ID, title, status badge
- Task count matches badge on card
- If no linked tasks: "No linked tasks" message
- Tasks clickable (if implemented)

**Notes:**
_______________________________________________________________

---

### TEST-MODAL-006: Modal Responsiveness
- [ ] **PASS** / [ ] **FAIL**

**Description:** Verify modal adapts to screen size
**Steps:**
1. Open modal on desktop (wide screen)
2. Resize browser to tablet width
3. Resize to mobile width

**Expected Result:**
- Desktop: Modal centered, reasonable width (max 800px)
- Tablet: Modal fills most of screen with margins
- Mobile: Modal full-width with padding
- All content readable at all sizes
- Scrollable when content exceeds viewport

**Notes:**
_______________________________________________________________

---

## 4. Filtering & Search

### TEST-FILTER-001: Type Dropdown Filter
- [ ] **PASS** / [ ] **FAIL**

**Description:** Verify entity type dropdown filters correctly
**Steps:**
1. Locate type filter dropdown
2. Select "file" from dropdown
3. Verify only file entities display
4. Select "other" from dropdown
5. Verify only other entities display
6. Select "all" to reset

**Expected Result:**
- Dropdown shows: All, File, Other
- Selecting type filters cards immediately
- Card count updates
- Empty state if no entities of type
- Filter persists until changed

**Notes:**
_______________________________________________________________

---

### TEST-FILTER-002: Tag Filters
- [ ] **PASS** / [ ] **FAIL**

**Description:** Verify tag filtering works
**Steps:**
1. Locate tag filter UI
2. Select a tag from available tags
3. Verify filtered results
4. Add second tag (if multi-select)
5. Clear tag filters

**Expected Result:**
- Tags displayed as clickable chips/buttons
- Clicking tag filters entities
- Multiple tags combine (AND or OR logic)
- Active tags highlighted
- Clear button removes all tag filters

**Notes:**
_______________________________________________________________

---

### TEST-FILTER-003: Search Bar Functionality
- [ ] **PASS** / [ ] **FAIL**

**Description:** Verify search bar filters by name/identifier
**Steps:**
1. Type partial entity name in search box
2. Wait for debounce (~300ms)
3. Verify results filter
4. Clear search box
5. Type identifier value
6. Verify results filter

**Expected Result:**
- Search box prominent and accessible
- Debouncing prevents excessive filtering
- Searches both name and identifier fields
- Case-insensitive search
- Results update smoothly
- Clear X button appears in search box

**Notes:**
_______________________________________________________________

---

### TEST-FILTER-004: Clear Filters Button
- [ ] **PASS** / [ ] **FAIL**

**Description:** Verify clear all filters button works
**Steps:**
1. Apply multiple filters (type, tags, search)
2. Click "Clear Filters" or reset button
3. Verify all filters removed

**Expected Result:**
- Clear button visible when filters active
- Clicking clears all active filters
- All entities redisplay
- Search box clears
- Type dropdown resets to "All"
- Tags deselected

**Notes:**
_______________________________________________________________

---

### TEST-FILTER-005: Filter Chips Display
- [ ] **PASS** / [ ] **FAIL**

**Description:** Verify active filters shown as removable chips
**Steps:**
1. Apply filters (type, tags, search)
2. Check for filter chip display
3. Click X on individual chip to remove

**Expected Result:**
- Active filters shown as chips/badges
- Each chip shows filter type and value
- X button on each chip
- Clicking X removes that filter only
- Chips visually distinct from tags

**Notes:**
_______________________________________________________________

---

## 5. Statistics Panel

### TEST-STATS-001: Stats Display
- [ ] **PASS** / [ ] **FAIL**

**Description:** Verify statistics panel shows correct data
**Steps:**
1. Locate statistics panel (sidebar or top)
2. Check displayed statistics
3. Manually count entities to verify

**Expected Result:**
Statistics show:
- Total entities count
- File entities count
- Other entities count
- Percentage breakdown
- Numbers match actual data

**Notes:**
_______________________________________________________________

---

### TEST-STATS-002: Percentages Calculation
- [ ] **PASS** / [ ] **FAIL**

**Description:** Verify percentage calculations are accurate
**Steps:**
1. Note total entities count
2. Note file and other counts
3. Verify percentages add to 100%
4. Calculate manually to confirm

**Expected Result:**
- Percentages accurate to 1 decimal place
- File % + Other % = 100%
- No rounding errors
- Display format: "42.5%" or similar

**Notes:**
_______________________________________________________________

---

### TEST-STATS-003: Top Tags Display
- [ ] **PASS** / [ ] **FAIL**

**Description:** Verify top tags section shows most common tags
**Steps:**
1. Locate "Top Tags" section in stats
2. Note displayed tags and counts
3. Verify against actual tag frequency

**Expected Result:**
- Shows top 5-10 most common tags
- Each tag shows usage count
- Tags sorted by frequency (highest first)
- Clickable to filter by tag

**Notes:**
_______________________________________________________________

---

## 6. Pagination

### TEST-PAGE-001: Previous/Next Buttons
- [ ] **PASS** / [ ] **FAIL**

**Description:** Verify pagination buttons work correctly
**Steps:**
1. Ensure enough entities for pagination (>10)
2. Click "Next" button
3. Verify page 2 loads
4. Click "Previous" button
5. Verify page 1 loads

**Expected Result:**
- Next button loads next page of results
- Previous button loads previous page
- Buttons disabled when at first/last page
- Page number updates
- Smooth transition between pages

**Notes:**
_______________________________________________________________

---

### TEST-PAGE-002: Page Numbers Display
- [ ] **PASS** / [ ] **FAIL**

**Description:** Verify page numbers and indicators display
**Steps:**
1. Check pagination UI for page numbers
2. Navigate through multiple pages
3. Check current page indicator

**Expected Result:**
- Current page number highlighted
- Total pages shown (e.g., "Page 2 of 5")
- Page numbers clickable (if displayed)
- Ellipsis for many pages (1 ... 5 6 7 ... 20)

**Notes:**
_______________________________________________________________

---

### TEST-PAGE-003: Page Size Selector
- [ ] **PASS** / [ ] **FAIL**

**Description:** Verify items-per-page selector works
**Steps:**
1. Locate page size dropdown (10, 25, 50, 100)
2. Select 25 items per page
3. Verify card count updates
4. Check pagination adjusts

**Expected Result:**
- Page size options: 10, 25, 50, 100
- Selecting size updates cards displayed
- Pagination recalculates total pages
- Current page resets to 1 (or stays valid)
- Selection persists across filters

**Notes:**
_______________________________________________________________

---

### TEST-PAGE-004: Results Summary
- [ ] **PASS** / [ ] **FAIL**

**Description:** Verify results summary text is accurate
**Steps:**
1. Check results summary (e.g., "Showing 1-10 of 42")
2. Navigate to page 2
3. Verify summary updates (e.g., "Showing 11-20 of 42")
4. Change page size and verify

**Expected Result:**
- Summary shows: "Showing X-Y of Z"
- X = first item number on page
- Y = last item number on page
- Z = total matching items
- Updates correctly with pagination and filters

**Notes:**
_______________________________________________________________

---

## 7. Responsive Design

### TEST-RESP-001: Mobile Layout (< 768px)
- [ ] **PASS** / [ ] **FAIL**

**Description:** Verify layout adapts to mobile screens
**Steps:**
1. Resize browser to mobile width (375px, 414px)
2. Or use browser dev tools device emulation
3. Check layout changes

**Expected Result:**
- Single column layout (1 card width)
- Navigation tabs stack or compress
- Filters accessible (collapsible/expandable)
- Cards full width with padding
- Text readable without zooming
- Touch targets large enough (44px min)

**Notes:**
_______________________________________________________________

---

### TEST-RESP-002: Tablet Layout (768px - 1024px)
- [ ] **PASS** / [ ] **FAIL**

**Description:** Verify layout adapts to tablet screens
**Steps:**
1. Resize browser to tablet width (768px, 1024px)
2. Check grid layout

**Expected Result:**
- Two-column grid layout
- Cards distributed evenly
- Filters visible (may be sidebar)
- Stats panel accessible
- No horizontal scrolling
- All content fits viewport width

**Notes:**
_______________________________________________________________

---

### TEST-RESP-003: Desktop Layout (> 1024px)
- [ ] **PASS** / [ ] **FAIL**

**Description:** Verify layout on desktop screens
**Steps:**
1. View on desktop width (1280px, 1920px)
2. Check maximum content width

**Expected Result:**
- Three-column grid layout (or more)
- Content centered with max-width (~1400px)
- Sidebar for filters/stats
- Generous spacing
- Cards not overly stretched
- Professional appearance

**Notes:**
_______________________________________________________________

---

### TEST-RESP-004: Responsive Modal
- [ ] **PASS** / [ ] **FAIL**

**Description:** Verify modal responsive behavior
**Steps:**
1. Open modal on mobile device
2. Check modal sizing
3. Test on tablet and desktop

**Expected Result:**
- Mobile: Full-screen modal or near full-screen
- Tablet: Modal with margins
- Desktop: Centered modal, max 800px width
- All sizes: Content scrollable if needed
- Close button always accessible

**Notes:**
_______________________________________________________________

---

## 8. Accessibility

### TEST-A11Y-001: Keyboard Navigation
- [ ] **PASS** / [ ] **FAIL**

**Description:** Verify full keyboard navigation support
**Steps:**
1. Use only keyboard (no mouse)
2. Tab through all interactive elements
3. Navigate tabs, filters, cards, modal
4. Verify focus indicators visible

**Expected Result:**
- Tab key moves focus logically
- Shift+Tab moves backward
- Enter/Space activates buttons/links
- ESC closes modal
- Focus indicators clearly visible (outline/ring)
- No keyboard traps
- Skip to content link (optional but recommended)

**Notes:**
_______________________________________________________________

---

### TEST-A11Y-002: ARIA Labels
- [ ] **PASS** / [ ] **FAIL**

**Description:** Verify ARIA labels present on interactive elements
**Steps:**
1. Inspect HTML source or use browser accessibility inspector
2. Check key elements for ARIA attributes

**Expected Result:**
Elements have appropriate ARIA:
- Buttons: aria-label or aria-labelledby
- Navigation: role="navigation"
- Tabs: role="tablist", "tab", "tabpanel"
- Modal: role="dialog", aria-modal="true"
- Close buttons: aria-label="Close"
- Search: aria-label="Search entities"

**Notes:**
_______________________________________________________________

---

### TEST-A11Y-003: Focus Management
- [ ] **PASS** / [ ] **FAIL**

**Description:** Verify focus managed correctly in modal
**Steps:**
1. Open modal using keyboard (Tab to card, press Enter)
2. Verify focus moves into modal
3. Tab through modal elements
4. Close modal
5. Verify focus returns to trigger element

**Expected Result:**
- Opening modal moves focus inside
- Focus trapped in modal (can't tab to background)
- Closing modal returns focus to card that opened it
- Logical tab order within modal

**Notes:**
_______________________________________________________________

---

### TEST-A11Y-004: Screen Reader Compatibility
- [ ] **PASS** / [ ] **FAIL**

**Description:** Verify screen reader announces content correctly
**Steps:**
1. Enable screen reader (NVDA, JAWS, VoiceOver)
2. Navigate through entities view
3. Listen to announcements

**Expected Result:**
- Tab names announced
- Entity count announced
- Card information read in logical order
- Type badges announced ("File entity", "Other entity")
- Modal title and content announced
- Buttons clearly identified
- Status messages announced (filter applied, etc.)

**Notes:**
_______________________________________________________________

---

### TEST-A11Y-005: Color Contrast
- [ ] **PASS** / [ ] **FAIL**

**Description:** Verify color contrast meets WCAG AA standards
**Steps:**
1. Use browser color contrast checker
2. Check text on backgrounds
3. Check type badges, buttons, links

**Expected Result:**
- Normal text: 4.5:1 contrast ratio minimum
- Large text (18pt+): 3:1 contrast ratio minimum
- Type badges readable
- Links distinguishable
- Focus indicators visible (3:1 ratio)

**Notes:**
_______________________________________________________________

---

## 9. Dark Mode

### TEST-DARK-001: Dark Mode Toggle
- [ ] **PASS** / [ ] **FAIL**

**Description:** Verify dark mode toggle switches theme
**Steps:**
1. Locate dark mode toggle (if present)
2. Click to switch to dark mode
3. Click to switch back to light mode

**Expected Result:**
- Toggle button clearly visible
- Clicking switches entire UI theme
- Preference saved (persists on reload)
- Smooth transition animation
- Icon changes (sun/moon)

**Notes:**
_______________________________________________________________

---

### TEST-DARK-002: Entity Cards in Dark Mode
- [ ] **PASS** / [ ] **FAIL**

**Description:** Verify entity cards display correctly in dark mode
**Steps:**
1. Enable dark mode
2. Check entity card appearance
3. Verify text readability

**Expected Result:**
- Card background dark (not pure black)
- Text light colored and readable
- Type badges adjusted for dark mode
- Hover effects visible
- No contrast issues

**Notes:**
_______________________________________________________________

---

### TEST-DARK-003: Modal in Dark Mode
- [ ] **PASS** / [ ] **FAIL**

**Description:** Verify modal displays correctly in dark mode
**Steps:**
1. Enable dark mode
2. Open entity detail modal
3. Check all modal sections

**Expected Result:**
- Modal background dark
- Modal header/footer dark
- Text readable (high contrast)
- Backdrop darker
- JSON syntax highlighting adjusted
- No white flashes

**Notes:**
_______________________________________________________________

---

### TEST-DARK-004: Filters & Controls in Dark Mode
- [ ] **PASS** / [ ] **FAIL**

**Description:** Verify filters and controls work in dark mode
**Steps:**
1. Enable dark mode
2. Check dropdowns, search box, buttons
3. Test interactive states

**Expected Result:**
- Dropdown menus dark themed
- Search box background dark
- Buttons appropriately colored
- Active filters clearly visible
- Hover/focus states visible
- No contrast issues on interactive elements

**Notes:**
_______________________________________________________________

---

### TEST-DARK-005: Dark Mode Consistency
- [ ] **PASS** / [ ] **FAIL**

**Description:** Verify dark mode consistent across all components
**Steps:**
1. Enable dark mode
2. Navigate through all UI sections
3. Check for any light mode leaks

**Expected Result:**
- All components use dark theme
- No white flashes or light backgrounds
- Consistent color palette throughout
- Stats panel dark themed
- Pagination controls dark themed
- No missed elements

**Notes:**
_______________________________________________________________

---

## Test Summary

**Total Test Cases:** 60

**Categories:**
1. Entities Tab Navigation: 4 tests
2. Entity Cards Display: 5 tests
3. Entity Detail Modal: 6 tests
4. Filtering & Search: 5 tests
5. Statistics Panel: 3 tests
6. Pagination: 4 tests
7. Responsive Design: 4 tests
8. Accessibility: 5 tests
9. Dark Mode: 5 tests

**Test Results:**
- Total Tests: 60
- Passed: _____
- Failed: _____
- Not Applicable: _____
- Pass Rate: _____%

---

## Issues Found

### Critical Issues
| Issue ID | Test Case | Description | Severity | Status |
|----------|-----------|-------------|----------|--------|
|          |           |             |          |        |

### Medium Issues
| Issue ID | Test Case | Description | Severity | Status |
|----------|-----------|-------------|----------|--------|
|          |           |             |          |        |

### Minor Issues
| Issue ID | Test Case | Description | Severity | Status |
|----------|-----------|-------------|----------|--------|
|          |           |             |          |        |

---

## Browser Compatibility Testing

Test on multiple browsers:

### Chrome/Chromium
- [ ] Desktop
- [ ] Mobile (Android)

### Firefox
- [ ] Desktop
- [ ] Mobile (Android)

### Safari
- [ ] Desktop (macOS)
- [ ] Mobile (iOS)

### Edge
- [ ] Desktop

---

## Performance Notes

**Page Load Time:** _________________
**Entity Card Render Time:** _________________
**Modal Open Time:** _________________
**Filter/Search Response Time:** _________________

**Performance Issues:**
_______________________________________________________________
_______________________________________________________________

---

## Recommendations

Based on testing results, document recommendations for:
1. Bug fixes required
2. UX improvements
3. Accessibility enhancements
4. Performance optimizations
5. Documentation updates

_______________________________________________________________
_______________________________________________________________
_______________________________________________________________

---

## Sign-Off

**Tester Name:** _________________
**Date Completed:** _________________
**Overall Assessment:** [ ] PASS / [ ] CONDITIONAL PASS / [ ] FAIL

**Notes:**
_______________________________________________________________
_______________________________________________________________

---

**End of Testing Checklist**
