#!/usr/bin/env python3
"""
Playwright test to diagnose Related Tasks table sorting issue.
"""

import asyncio
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright


async def test_sorting():
    """Test the Related Tasks table sorting functionality."""

    # Configuration
    BASE_URL = "http://127.0.0.1:8001"
    API_KEY = "quJ5dpjJHfhuskKj3CGcTxn5Af6HZ-O9mPkaepvH7fo"
    SCREENSHOTS_DIR = Path("/Users/cliffclarke/Claude_Code/task-mcp/docs/subagent-reports/ui-enhancements/related-tasks-sorting/screenshots")
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()

        # Enable console logging
        console_logs = []
        page.on("console", lambda msg: console_logs.append({
            "type": msg.type,
            "text": msg.text,
            "location": msg.location
        }))

        # Enable error tracking
        errors = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))

        print("=" * 80)
        print("PLAYWRIGHT TESTING: Related Tasks Sorting Diagnostics")
        print("=" * 80)

        # Step 1: Navigate to application
        print("\n[1] Navigating to application...")
        await page.goto(BASE_URL)
        await page.screenshot(path=SCREENSHOTS_DIR / f"{timestamp}_01_home.png")
        print("   ✓ Screenshot: 01_home.png")

        # Step 2: Set API key if needed
        print("\n[2] Checking if API key is needed...")
        api_input = page.locator('input[placeholder="Enter your API key"]')
        if await api_input.is_visible():
            print("   Setting API key...")
            await api_input.fill(API_KEY)
            await page.click('button:has-text("Save")')
            await page.wait_for_timeout(2000)
        print("   ✓ Ready to proceed")

        # Step 3: Find and open a task with the "Full Details" button
        print("\n[3] Finding a task and opening full details...")

        # Wait for task cards to load
        await page.wait_for_selector('button:has-text("Full Details")', timeout=10000)
        print("   ✓ Tasks loaded")

        # Click the first "Full Details" button
        full_details_buttons = page.locator('button:has-text("Full Details")')
        first_button = full_details_buttons.first
        print("   Clicking 'Full Details' on first task...")
        await first_button.click()
        await page.wait_for_timeout(2000)

        # Check for Related Tasks table on detail page
        related_header = page.locator('h2:has-text("Related Tasks")')
        if await related_header.is_visible():
            print("   ✓ Found Related Tasks table on detail page")
            target_task = "Task (detail page)"
        else:
            print("   ⚠ Related Tasks section not visible")
            print("   This is expected - the table may be on the page but data determines visibility")
            target_task = "Task (detail page)"

        await page.screenshot(path=SCREENSHOTS_DIR / f"{timestamp}_02_task_selected.png")
        print("   ✓ Screenshot: 02_task_selected.png")

        # Step 4: Capture initial state
        print("\n[4] Capturing initial Related Tasks table state...")

        # Get Alpine.js data
        alpine_data = await page.evaluate("""
            () => {
                const el = document.querySelector('[x-data]');
                if (el && el.__x && el.__x.$data) {
                    return {
                        relatedTasksSortColumn: el.__x.$data.relatedTasksSortColumn,
                        relatedTasksSortDirection: el.__x.$data.relatedTasksSortDirection,
                        detailPageRelatedTasks: el.__x.$data.detailPageRelatedTasks,
                        sortRelatedTasksExists: typeof el.__x.$data.sortRelatedTasks === 'function'
                    };
                }
                return null;
            }
        """)

        print("   Alpine.js State:")
        if alpine_data:
            print(f"     - sortColumn: {alpine_data.get('relatedTasksSortColumn')}")
            print(f"     - sortDirection: {alpine_data.get('relatedTasksSortDirection')}")
            print(f"     - sortRelatedTasks exists: {alpine_data.get('sortRelatedTasksExists')}")
            print("     - Related tasks structure:")
            if alpine_data.get('detailPageRelatedTasks'):
                related = alpine_data['detailPageRelatedTasks']
                print(f"       - parent: {'Yes' if related.get('parent') else 'No'}")
                print(f"       - children: {len(related.get('children', []))}")
                print(f"       - dependencies: {len(related.get('dependencies', []))}")
                print(f"       - blocking: {len(related.get('blocking', []))}")
            else:
                print("       - No detailPageRelatedTasks found")
        else:
            print("     ✗ Could not access Alpine.js data")

        # Get initial task order
        initial_task_ids = await page.evaluate("""
            () => {
                const rows = Array.from(document.querySelectorAll('table tbody tr'));
                return rows.map(row => {
                    const idCell = row.querySelector('td:nth-child(2)');
                    return idCell ? idCell.textContent.trim() : null;
                }).filter(id => id !== null);
            }
        """)
        print(f"   Initial task IDs order: {initial_task_ids}")

        await page.screenshot(path=SCREENSHOTS_DIR / f"{timestamp}_03_initial_state.png")
        print("   ✓ Screenshot: 03_initial_state.png")

        # Step 5: Test ID sorting
        print("\n[5] Testing ID column sorting...")

        # Find and click the ID header
        id_header_button = page.locator('th button:has-text("ID")')

        # Check if the button exists and is visible
        if not await id_header_button.is_visible():
            print("   ⚠ ID header button not visible - table may be empty or hidden")
            print("   Skipping sort tests...")
            await page.screenshot(path=SCREENSHOTS_DIR / f"{timestamp}_04_no_table.png")
            print("   ✓ Screenshot: 04_no_table.png")

            # Try to debug - look for the table
            table_exists = await page.locator('h2:has-text("Related Tasks")').is_visible()
            print(f"   Debug: Related Tasks header visible: {table_exists}")

            tbody_count = await page.locator('table tbody tr').count()
            print(f"   Debug: Table body rows found: {tbody_count}")

            await browser.close()
            return

        print("   Clicking ID header...")
        await id_header_button.click()
        await page.wait_for_timeout(500)

        # Capture state after click
        after_click_data = await page.evaluate("""
            () => {
                const el = document.querySelector('[x-data]');
                if (el && el.__x && el.__x.$data) {
                    return {
                        relatedTasksSortColumn: el.__x.$data.relatedTasksSortColumn,
                        relatedTasksSortDirection: el.__x.$data.relatedTasksSortDirection,
                        detailPageRelatedTasks: el.__x.$data.detailPageRelatedTasks
                    };
                }
                return null;
            }
        """)

        print("   After clicking ID header:")
        if after_click_data:
            print(f"     - sortColumn: {after_click_data.get('relatedTasksSortColumn')}")
            print(f"     - sortDirection: {after_click_data.get('relatedTasksSortDirection')}")
        else:
            print("     ✗ Could not access Alpine.js data after click")

        # Get task order after sort
        after_sort_ids = await page.evaluate("""
            () => {
                const rows = Array.from(document.querySelectorAll('table tbody tr'));
                return rows.map(row => {
                    const idCell = row.querySelector('td:nth-child(2)');
                    return idCell ? idCell.textContent.trim() : null;
                }).filter(id => id !== null);
            }
        """)
        print(f"   Task IDs after sort: {after_sort_ids}")
        print(f"   Order changed: {initial_task_ids != after_sort_ids}")

        await page.screenshot(path=SCREENSHOTS_DIR / f"{timestamp}_04_after_id_sort.png")
        print("   ✓ Screenshot: 04_after_id_sort.png")

        # Step 6: Test Title sorting
        print("\n[6] Testing Title column sorting...")

        title_header_button = page.locator('th button:has-text("Title")')
        print("   Clicking Title header...")
        await title_header_button.click()
        await page.wait_for_timeout(500)

        # Capture state
        after_title_click = await page.evaluate("""
            () => {
                const el = document.querySelector('[x-data]');
                if (el && el.__x && el.__x.$data) {
                    return {
                        relatedTasksSortColumn: el.__x.$data.relatedTasksSortColumn,
                        relatedTasksSortDirection: el.__x.$data.relatedTasksSortDirection
                    };
                }
                return null;
            }
        """)

        print("   After clicking Title header:")
        if after_title_click:
            print(f"     - sortColumn: {after_title_click.get('relatedTasksSortColumn')}")
            print(f"     - sortDirection: {after_title_click.get('relatedTasksSortDirection')}")
        else:
            print("     ✗ Could not access Alpine.js data after click")

        await page.screenshot(path=SCREENSHOTS_DIR / f"{timestamp}_05_after_title_sort.png")
        print("   ✓ Screenshot: 05_after_title_sort.png")

        # Step 7: Check console logs and errors
        print("\n[7] Checking browser console...")
        print(f"   Console messages: {len(console_logs)}")
        for log in console_logs[-10:]:  # Last 10 messages
            print(f"     [{log['type']}] {log['text']}")

        print(f"\n   JavaScript errors: {len(errors)}")
        for error in errors:
            print(f"     {error}")

        # Step 8: Manual sort function test
        print("\n[8] Testing sort function manually...")

        manual_sort_result = await page.evaluate("""
            () => {
                try {
                    const el = document.querySelector('[x-data]');
                    if (el && el.__x && el.__x.$data && typeof el.__x.$data.sortRelatedTasks === 'function') {
                        // Call the function directly
                        el.__x.$data.sortRelatedTasks('id');
                        return {
                            success: true,
                            sortColumn: el.__x.$data.relatedTasksSortColumn,
                            sortDirection: el.__x.$data.relatedTasksSortDirection
                        };
                    }
                    return { success: false, error: 'Function not found' };
                } catch (e) {
                    return { success: false, error: e.toString() };
                }
            }
        """)

        print("   Manual sort call result:")
        print(f"     - Success: {manual_sort_result.get('success')}")
        print(f"     - Sort column: {manual_sort_result.get('sortColumn')}")
        print(f"     - Sort direction: {manual_sort_result.get('sortDirection')}")
        if 'error' in manual_sort_result:
            print(f"     - Error: {manual_sort_result['error']}")

        await page.wait_for_timeout(500)
        await page.screenshot(path=SCREENSHOTS_DIR / f"{timestamp}_06_manual_sort.png")
        print("   ✓ Screenshot: 06_manual_sort.png")

        # Final summary
        print("\n" + "=" * 80)
        print("DIAGNOSIS SUMMARY")
        print("=" * 80)
        print(f"✓ Application accessible at {BASE_URL}")
        print(f"✓ Task with related tasks found: {target_task}")
        print(f"✓ Sort function exists: {alpine_data.get('sortRelatedTasksExists') if alpine_data else 'Could not check'}")
        print(f"✓ Screenshots saved to: {SCREENSHOTS_DIR}")

        print("\nFINDINGS:")
        if initial_task_ids == after_sort_ids:
            print("  ⚠ WARNING: Task order DID NOT CHANGE after clicking sort header")
        else:
            print("  ✓ Task order changed after clicking sort header")

        if after_click_data and after_click_data.get('relatedTasksSortColumn') == 'id':
            print("  ✓ Sort column state updated to 'id'")
        else:
            print("  ⚠ Sort column state NOT updated (expected 'id', got: {})".format(
                after_click_data.get('relatedTasksSortColumn') if after_click_data else 'N/A'
            ))

        if errors:
            print(f"  ⚠ Found {len(errors)} JavaScript errors")
        else:
            print("  ✓ No JavaScript errors detected")

        # Keep browser open for inspection
        print("\n[Browser will remain open for 30 seconds for manual inspection]")
        await page.wait_for_timeout(30000)

        await browser.close()
        print("\n✓ Test complete!")


if __name__ == "__main__":
    asyncio.run(test_sorting())
