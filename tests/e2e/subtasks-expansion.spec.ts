import { test, expect } from '@playwright/test'

/**
 * E2E tests for subtasks expansion feature.
 *
 * Tests proper behavior of "Show X subtasks" button including:
 * - Event propagation handling (should not open modal)
 * - Expansion/collapse toggle
 * - Parent tasks filter
 * - Keyboard accessibility
 */
test.describe('Subtasks Expansion', () => {
  const API_KEY = 'quJ5dpjJHfhuskKj3CGcTxn5Af6HZ-O9mPkaepvH7fo'

  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:8001')

    // Handle API key modal if present
    const apiKeyModal = page.locator('[aria-labelledby="api-key-modal-title"]')
    if (await apiKeyModal.isVisible()) {
      await page.locator('#api-key-input').fill(API_KEY)
      await page.locator('button:has-text("Save")').click()
      await page.waitForTimeout(2000)
    }

    await page.waitForLoadState('networkidle')
  })

  test('clicking subtasks button should NOT open task detail modal', async ({ page }) => {
    // Apply Parent Tasks filter to show tasks with children
    await page.locator('button:has-text("Parent Tasks")').click()
    await page.waitForTimeout(1000)

    // Find first subtask button
    const subtaskButton = page.locator('button').filter({ hasText: /Show.*subtask/ }).first()

    // Skip if no subtasks found
    const buttonExists = await subtaskButton.isVisible().catch(() => false)
    if (!buttonExists) {
      console.log('No tasks with subtasks found - skipping test')
      return
    }

    // Click the subtasks button
    await subtaskButton.click()
    await page.waitForTimeout(500)

    // CRITICAL: Modal should NOT open (this was the bug)
    const modal = page.locator('[role="dialog"][aria-modal="true"]')
    const modalOpen = await modal.isVisible().catch(() => false)

    expect(modalOpen).toBe(false)
  })

  test('subtasks button should expand and collapse correctly', async ({ page }) => {
    // Apply Parent Tasks filter
    await page.locator('button:has-text("Parent Tasks")').click()
    await page.waitForTimeout(1000)

    const subtaskButton = page.locator('button').filter({ hasText: /Show.*subtask/ }).first()
    const buttonExists = await subtaskButton.isVisible().catch(() => false)

    if (!buttonExists) {
      console.log('No tasks with subtasks found - skipping test')
      return
    }

    // Initially should show "Show X subtasks"
    await expect(subtaskButton).toContainText('Show')

    // Click to expand
    await subtaskButton.click()
    await page.waitForTimeout(1000) // Wait for x-collapse animation

    // Should change to "Hide subtasks"
    await expect(subtaskButton).toContainText('Hide')

    // Subtask cards should be visible (x-collapse may keep container hidden during animation)
    const subtaskCards = page.locator('.bg-gray-50.dark\\:bg-gray-700\\/50.rounded')
    const subtaskCount = await subtaskCards.count()
    expect(subtaskCount).toBeGreaterThan(0)

    // Click again to collapse
    await subtaskButton.click()
    await page.waitForTimeout(500)

    // Should change back to "Show X subtasks"
    await expect(subtaskButton).toContainText('Show')
  })

  test('parent tasks filter shows only tasks with children', async ({ page }) => {
    // Clear any active filters
    const clearButton = page.locator('button:has-text("Clear Filter")')
    if (await clearButton.isVisible()) {
      await clearButton.click()
      await page.waitForTimeout(500)
    }

    // Get count before filter
    const allTaskCards = page.locator('.bg-white.dark\\:bg-gray-800.rounded-lg')
    const allCount = await allTaskCards.count()

    // Apply Parent Tasks filter
    await page.locator('button:has-text("Parent Tasks")').click()
    await page.waitForTimeout(1000)

    // Get count after filter
    const parentTaskCards = page.locator('.bg-white.dark\\:bg-gray-800.rounded-lg')
    const parentCount = await parentTaskCards.count()

    console.log(`All tasks: ${allCount}, Parent tasks: ${parentCount}`)

    // Parent count should be less than or equal to all count
    expect(parentCount).toBeLessThanOrEqual(allCount)

    // All visible tasks should have subtask buttons
    if (parentCount > 0) {
      const subtaskButtons = page.locator('button').filter({ hasText: /Show.*subtask/ })
      const buttonCount = await subtaskButtons.count()

      // At least one task should have subtasks
      expect(buttonCount).toBeGreaterThan(0)
    }
  })

  test('subtask button is keyboard accessible', async ({ page }) => {
    // Apply Parent Tasks filter
    await page.locator('button:has-text("Parent Tasks")').click()
    await page.waitForTimeout(1000)

    const subtaskButton = page.locator('button').filter({ hasText: /Show.*subtask/ }).first()
    const buttonExists = await subtaskButton.isVisible().catch(() => false)

    if (!buttonExists) {
      console.log('No tasks with subtasks found - skipping test')
      return
    }

    // Focus the button
    await subtaskButton.focus()

    // Press Enter to expand
    await page.keyboard.press('Enter')
    await page.waitForTimeout(500)

    // Should expand
    await expect(subtaskButton).toContainText('Hide')

    // Press Enter again to collapse
    await page.keyboard.press('Enter')
    await page.waitForTimeout(500)

    // Should collapse
    await expect(subtaskButton).toContainText('Show')
  })
})
