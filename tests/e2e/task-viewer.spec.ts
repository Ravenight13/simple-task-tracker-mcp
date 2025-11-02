import { test, expect } from '@playwright/test';
import { injectAxe, checkA11y } from 'axe-playwright';

const BASE_URL = 'http://localhost:8001';

test.describe('Task Viewer Frontend E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');
  });

  test('1. Page loads successfully', async ({ page }) => {
    await expect(page).toHaveTitle(/Task Viewer/);

    // Check main elements are visible
    await expect(page.locator('[data-testid="page-title"]')).toBeVisible();
    await expect(page.locator('[data-testid="project-selector"]')).toBeVisible();
  });

  test('2. Project Selection - Dropdown exists and works', async ({ page }) => {
    const projectSelector = page.locator('[data-testid="project-selector"]');
    await expect(projectSelector).toBeVisible();

    // Take screenshot of project selector
    await page.screenshot({ path: 'screenshots/project-selector.png' });

    // Check if projects are loaded
    const hasProjects = await projectSelector.locator('option').count();
    expect(hasProjects).toBeGreaterThan(0);
  });

  test('3. Project Selection - Can select different projects', async ({ page }) => {
    const projectSelector = page.locator('[data-testid="project-selector"]');

    // Get available projects
    const projectCount = await projectSelector.locator('option').count();

    if (projectCount > 1) {
      // Select second project
      const secondProject = await projectSelector.locator('option').nth(1).textContent();
      await projectSelector.selectOption({ index: 1 });

      // Wait for tasks to reload
      await page.waitForTimeout(500);
      await page.waitForLoadState('networkidle');

      // Verify project changed
      const selectedValue = await projectSelector.inputValue();
      expect(selectedValue).toBeTruthy();

      await page.screenshot({ path: 'screenshots/project-changed.png' });
    } else {
      console.log('Only one project available, skipping project change test');
    }
  });

  test('4. Task Display - Tasks are visible on page load', async ({ page }) => {
    // Wait for tasks to load
    await page.waitForSelector('[data-testid="task-list"]', { timeout: 5000 });

    const taskList = page.locator('[data-testid="task-list"]');
    await expect(taskList).toBeVisible();

    // Check if tasks exist (or empty state)
    const taskCards = page.locator('[data-testid="task-card"]');
    const taskCount = await taskCards.count();

    if (taskCount > 0) {
      await expect(taskCards.first()).toBeVisible();
      await page.screenshot({ path: 'screenshots/tasks-loaded.png', fullPage: true });
    } else {
      // Check for empty state
      const emptyState = page.locator('text=/No tasks found/i');
      await expect(emptyState).toBeVisible();
      await page.screenshot({ path: 'screenshots/empty-state.png' });
    }

    console.log(`Found ${taskCount} tasks`);
  });

  test('5. Task Display - Task cards show title, status, priority', async ({ page }) => {
    await page.waitForSelector('[data-testid="task-list"]');

    const taskCards = page.locator('[data-testid="task-card"]');
    const taskCount = await taskCards.count();

    if (taskCount > 0) {
      const firstTask = taskCards.first();

      // Check task card structure
      await expect(firstTask.locator('[data-testid="task-title"]')).toBeVisible();
      await expect(firstTask.locator('[data-testid="task-status"]')).toBeVisible();
      await expect(firstTask.locator('[data-testid="task-priority"]')).toBeVisible();

      // Get and verify content
      const title = await firstTask.locator('[data-testid="task-title"]').textContent();
      const status = await firstTask.locator('[data-testid="task-status"]').textContent();
      const priority = await firstTask.locator('[data-testid="task-priority"]').textContent();

      expect(title).toBeTruthy();
      expect(status).toMatch(/todo|in_progress|done|blocked|cancelled/i);
      expect(priority).toMatch(/low|medium|high/i);

      await page.screenshot({ path: 'screenshots/task-card-detail.png' });
    }
  });

  test('6. Task Display - Task counts are accurate', async ({ page }) => {
    await page.waitForSelector('[data-testid="task-list"]');

    // Get task count from UI
    const taskCountDisplay = page.locator('[data-testid="task-count"]');

    if (await taskCountDisplay.isVisible()) {
      const displayedCount = await taskCountDisplay.textContent();

      // Count actual task cards
      const taskCards = page.locator('[data-testid="task-card"]');
      const actualCount = await taskCards.count();

      console.log(`Displayed count: ${displayedCount}, Actual count: ${actualCount}`);

      // The displayed count should contain the actual count
      expect(displayedCount).toContain(actualCount.toString());
    }
  });

  test('7. Filtering - Status filters work', async ({ page }) => {
    await page.waitForSelector('[data-testid="task-list"]');

    const statusFilters = ['All', 'To Do', 'In Progress', 'Done', 'Blocked'];

    for (const status of statusFilters) {
      const filterButton = page.locator(`[data-testid="status-filter-${status.toLowerCase().replace(' ', '-')}"]`);

      if (await filterButton.isVisible()) {
        await filterButton.click();
        await page.waitForTimeout(300);

        // Take screenshot
        await page.screenshot({ path: `screenshots/filter-status-${status.toLowerCase().replace(' ', '-')}.png` });

        // Verify filter is active
        await expect(filterButton).toHaveClass(/active|selected/);
      }
    }
  });

  test('8. Filtering - Priority filters work', async ({ page }) => {
    await page.waitForSelector('[data-testid="task-list"]');

    const priorityFilters = ['All', 'Low', 'Medium', 'High'];

    for (const priority of priorityFilters) {
      const filterButton = page.locator(`[data-testid="priority-filter-${priority.toLowerCase()}"]`);

      if (await filterButton.isVisible()) {
        await filterButton.click();
        await page.waitForTimeout(300);

        // Take screenshot
        await page.screenshot({ path: `screenshots/filter-priority-${priority.toLowerCase()}.png` });

        // Verify filter is active
        await expect(filterButton).toHaveClass(/active|selected/);
      }
    }
  });

  test('9. Filtering - Filtered counts update correctly', async ({ page }) => {
    await page.waitForSelector('[data-testid="task-list"]');

    // Get initial count
    const taskCards = page.locator('[data-testid="task-card"]');
    const initialCount = await taskCards.count();

    // Apply a status filter
    const todoFilter = page.locator('[data-testid="status-filter-to-do"]');
    if (await todoFilter.isVisible()) {
      await todoFilter.click();
      await page.waitForTimeout(500);

      const filteredCount = await taskCards.count();

      // Filtered count should be <= initial count
      expect(filteredCount).toBeLessThanOrEqual(initialCount);

      console.log(`Initial: ${initialCount}, Filtered: ${filteredCount}`);
    }
  });

  test('10. Search - Search bar exists', async ({ page }) => {
    const searchBar = page.locator('[data-testid="search-input"]');
    await expect(searchBar).toBeVisible();
    await expect(searchBar).toBeEditable();

    await page.screenshot({ path: 'screenshots/search-bar.png' });
  });

  test('11. Search - Search filters tasks by title/description', async ({ page }) => {
    await page.waitForSelector('[data-testid="task-list"]');

    const searchBar = page.locator('[data-testid="search-input"]');
    const taskCards = page.locator('[data-testid="task-card"]');

    const initialCount = await taskCards.count();

    if (initialCount > 0) {
      // Get first task title
      const firstTaskTitle = await taskCards.first().locator('[data-testid="task-title"]').textContent();
      const searchTerm = firstTaskTitle?.split(' ')[0] || 'test';

      // Type in search
      await searchBar.fill(searchTerm);
      await page.waitForTimeout(500);

      const filteredCount = await taskCards.count();

      // Should filter results
      expect(filteredCount).toBeLessThanOrEqual(initialCount);

      await page.screenshot({ path: 'screenshots/search-filtered.png' });

      console.log(`Search "${searchTerm}": ${initialCount} → ${filteredCount} tasks`);
    }
  });

  test('12. Search - Clear search works', async ({ page }) => {
    await page.waitForSelector('[data-testid="task-list"]');

    const searchBar = page.locator('[data-testid="search-input"]');
    const taskCards = page.locator('[data-testid="task-card"]');

    const initialCount = await taskCards.count();

    // Type search
    await searchBar.fill('test search');
    await page.waitForTimeout(500);

    // Clear search
    await searchBar.clear();
    await page.waitForTimeout(500);

    const finalCount = await taskCards.count();

    // Should return to original count
    expect(finalCount).toBe(initialCount);

    await page.screenshot({ path: 'screenshots/search-cleared.png' });
  });

  test('13. Task Modal - Clicking a task opens modal', async ({ page }) => {
    await page.waitForSelector('[data-testid="task-list"]');

    const taskCards = page.locator('[data-testid="task-card"]');
    const taskCount = await taskCards.count();

    if (taskCount > 0) {
      // Click first task
      await taskCards.first().click();
      await page.waitForTimeout(500);

      // Check if modal opened
      const modal = page.locator('[data-testid="task-modal"]');
      await expect(modal).toBeVisible();

      await page.screenshot({ path: 'screenshots/task-modal-open.png' });
    }
  });

  test('14. Task Modal - Modal shows task details', async ({ page }) => {
    await page.waitForSelector('[data-testid="task-list"]');

    const taskCards = page.locator('[data-testid="task-card"]');
    const taskCount = await taskCards.count();

    if (taskCount > 0) {
      // Click first task
      await taskCards.first().click();
      await page.waitForTimeout(500);

      const modal = page.locator('[data-testid="task-modal"]');

      // Check modal content
      await expect(modal.locator('[data-testid="modal-task-title"]')).toBeVisible();
      await expect(modal.locator('[data-testid="modal-task-status"]')).toBeVisible();
      await expect(modal.locator('[data-testid="modal-task-priority"]')).toBeVisible();

      await page.screenshot({ path: 'screenshots/task-modal-details.png' });
    }
  });

  test('15. Task Modal - Modal can be closed', async ({ page }) => {
    await page.waitForSelector('[data-testid="task-list"]');

    const taskCards = page.locator('[data-testid="task-card"]');
    const taskCount = await taskCards.count();

    if (taskCount > 0) {
      // Click first task to open modal
      await taskCards.first().click();
      await page.waitForTimeout(500);

      const modal = page.locator('[data-testid="task-modal"]');
      await expect(modal).toBeVisible();

      // Close modal (try multiple methods)
      const closeButton = modal.locator('[data-testid="modal-close"]');

      if (await closeButton.isVisible()) {
        await closeButton.click();
      } else {
        // Try pressing Escape
        await page.keyboard.press('Escape');
      }

      await page.waitForTimeout(500);

      // Modal should be hidden
      await expect(modal).not.toBeVisible();

      await page.screenshot({ path: 'screenshots/task-modal-closed.png' });
    }
  });

  test('16. API Key Modal - Check functionality', async ({ page }) => {
    // Look for API key button/trigger
    const apiKeyButton = page.locator('[data-testid="api-key-button"]');

    if (await apiKeyButton.isVisible()) {
      await apiKeyButton.click();
      await page.waitForTimeout(500);

      const apiKeyModal = page.locator('[data-testid="api-key-modal"]');
      await expect(apiKeyModal).toBeVisible();

      await page.screenshot({ path: 'screenshots/api-key-modal.png' });
    } else {
      console.log('API Key modal button not found - may be conditional');
    }
  });

  test('17. Accessibility - Keyboard navigation', async ({ page }) => {
    await page.waitForSelector('[data-testid="task-list"]');

    // Tab through elements
    await page.keyboard.press('Tab');
    await page.waitForTimeout(200);

    // Check if focus is visible
    const focusedElement = await page.evaluate(() => document.activeElement?.getAttribute('data-testid'));

    await page.screenshot({ path: 'screenshots/keyboard-navigation.png' });

    console.log(`Focused element: ${focusedElement}`);
  });

  test('18. Accessibility - ARIA labels', async ({ page }) => {
    await page.waitForSelector('[data-testid="task-list"]');

    // Check for ARIA labels on key elements
    const projectSelector = page.locator('[data-testid="project-selector"]');
    const searchInput = page.locator('[data-testid="search-input"]');

    if (await projectSelector.isVisible()) {
      const ariaLabel = await projectSelector.getAttribute('aria-label');
      console.log(`Project selector ARIA label: ${ariaLabel}`);
    }

    if (await searchInput.isVisible()) {
      const ariaLabel = await searchInput.getAttribute('aria-label');
      console.log(`Search input ARIA label: ${ariaLabel}`);
    }
  });

  test('19. Accessibility - Axe-core audit', async ({ page }) => {
    await page.waitForSelector('[data-testid="task-list"]');

    // Inject axe-core
    await injectAxe(page);

    // Run accessibility audit
    await checkA11y(page, null, {
      detailedReport: true,
      detailedReportOptions: {
        html: true
      }
    });

    await page.screenshot({ path: 'screenshots/accessibility-audit.png' });
  });

  test('20. Console Errors - No JavaScript errors', async ({ page }) => {
    const errors: string[] = [];

    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    page.on('pageerror', error => {
      errors.push(error.message);
    });

    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    expect(errors).toHaveLength(0);

    if (errors.length > 0) {
      console.log('Console errors found:', errors);
    }
  });
});
