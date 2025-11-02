#!/usr/bin/env python3
"""
Playwright script to debug task-mcp task viewer frontend.
Captures console errors, Alpine.js expression errors, and network issues.
"""

import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright

async def debug_task_viewer():
    """Main debugging function to capture all frontend errors."""

    # Storage for captured errors
    console_logs = []
    console_errors = []
    console_warnings = []
    page_errors = []
    network_errors = []

    async with async_playwright() as p:
        # Launch browser with console logging
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()

        # Set up console message capture
        def handle_console(msg):
            msg_data = {
                'timestamp': datetime.now().isoformat(),
                'type': msg.type,
                'text': msg.text,
                'location': msg.location
            }

            if msg.type == 'error':
                console_errors.append(msg_data)
                print(f"❌ CONSOLE ERROR: {msg.text}")
            elif msg.type == 'warning':
                console_warnings.append(msg_data)
                print(f"⚠️  CONSOLE WARNING: {msg.text}")
            else:
                console_logs.append(msg_data)
                if 'Alpine' in msg.text or 'error' in msg.text.lower():
                    print(f"📝 CONSOLE LOG: {msg.text}")

        page.on('console', handle_console)

        # Set up page error capture
        def handle_page_error(error):
            error_data = {
                'timestamp': datetime.now().isoformat(),
                'message': str(error)
            }
            page_errors.append(error_data)
            print(f"🔥 PAGE ERROR: {error}")

        page.on('pageerror', handle_page_error)

        # Set up network failure capture
        def handle_request_failed(request):
            error_data = {
                'timestamp': datetime.now().isoformat(),
                'url': request.url,
                'method': request.method,
                'failure': request.failure
            }
            network_errors.append(error_data)
            print(f"🌐 NETWORK ERROR: {request.method} {request.url} - {request.failure}")

        page.on('requestfailed', handle_request_failed)

        print("\n" + "="*80)
        print("🚀 Starting Task Viewer Debugging Session")
        print("="*80 + "\n")

        # Navigate to the task viewer
        print("📍 Navigating to http://localhost:8001...")
        try:
            await page.goto('http://localhost:8001', wait_until='networkidle', timeout=10000)
            print("✅ Page loaded successfully\n")
        except Exception as e:
            print(f"❌ Failed to load page: {e}\n")
            await browser.close()
            return

        # Take initial screenshot
        await page.screenshot(path='/Users/cliffclarke/Claude_Code/task-mcp/debug_screenshots/01_initial_load.png')
        print("📸 Screenshot saved: 01_initial_load.png\n")

        # Wait a moment for Alpine.js to initialize
        await asyncio.sleep(2)

        # Take post-Alpine screenshot
        await page.screenshot(path='/Users/cliffclarke/Claude_Code/task-mcp/debug_screenshots/02_after_alpine_init.png')
        print("📸 Screenshot saved: 02_after_alpine_init.png\n")

        # Check if Alpine.js is loaded
        alpine_loaded = await page.evaluate('typeof Alpine !== "undefined"')
        print(f"🔍 Alpine.js loaded: {alpine_loaded}\n")

        # Get Alpine component data
        try:
            alpine_data = await page.evaluate('''() => {
                const el = document.querySelector('[x-data]');
                if (el && el._x_dataStack) {
                    return JSON.stringify(el._x_dataStack[0], null, 2);
                }
                return "No Alpine data found";
            }''')
            print(f"📊 Alpine Component Data:\n{alpine_data}\n")
        except Exception as e:
            print(f"❌ Failed to get Alpine data: {e}\n")

        # Try to interact with various elements
        print("🖱️  Testing interactions...\n")

        # Test 1: Click "All" filter
        try:
            await page.click('[data-testid="filter-all"]', timeout=2000)
            await asyncio.sleep(1)
            await page.screenshot(path='/Users/cliffclarke/Claude_Code/task-mcp/debug_screenshots/03_filter_all_clicked.png')
            print("✅ Clicked 'All' filter\n")
        except Exception as e:
            print(f"❌ Failed to click 'All' filter: {e}\n")

        # Test 2: Click "To Do" filter
        try:
            await page.click('[data-testid="filter-todo"]', timeout=2000)
            await asyncio.sleep(1)
            await page.screenshot(path='/Users/cliffclarke/Claude_Code/task-mcp/debug_screenshots/04_filter_todo_clicked.png')
            print("✅ Clicked 'To Do' filter\n")
        except Exception as e:
            print(f"❌ Failed to click 'To Do' filter: {e}\n")

        # Test 3: Click "In Progress" filter
        try:
            await page.click('[data-testid="filter-in_progress"]', timeout=2000)
            await asyncio.sleep(1)
            await page.screenshot(path='/Users/cliffclarke/Claude_Code/task-mcp/debug_screenshots/05_filter_in_progress_clicked.png')
            print("✅ Clicked 'In Progress' filter\n")
        except Exception as e:
            print(f"❌ Failed to click 'In Progress' filter: {e}\n")

        # Test 4: Click "Done" filter
        try:
            await page.click('[data-testid="filter-done"]', timeout=2000)
            await asyncio.sleep(1)
            await page.screenshot(path='/Users/cliffclarke/Claude_Code/task-mcp/debug_screenshots/06_filter_done_clicked.png')
            print("✅ Clicked 'Done' filter\n")
        except Exception as e:
            print(f"❌ Failed to click 'Done' filter: {e}\n")

        # Test 5: Try to expand a task (if any exist)
        try:
            task_rows = await page.query_selector_all('[data-testid^="task-row-"]')
            if task_rows:
                await task_rows[0].click(timeout=2000)
                await asyncio.sleep(1)
                await page.screenshot(path='/Users/cliffclarke/Claude_Code/task-mcp/debug_screenshots/07_task_expanded.png')
                print("✅ Clicked first task row\n")
            else:
                print("⚠️  No task rows found to click\n")
        except Exception as e:
            print(f"❌ Failed to click task row: {e}\n")

        # Test 6: Hover over priority badges
        try:
            priority_badges = await page.query_selector_all('[data-testid^="priority-"]')
            if priority_badges:
                await priority_badges[0].hover(timeout=2000)
                await asyncio.sleep(0.5)
                await page.screenshot(path='/Users/cliffclarke/Claude_Code/task-mcp/debug_screenshots/08_priority_hover.png')
                print("✅ Hovered over priority badge\n")
            else:
                print("⚠️  No priority badges found\n")
        except Exception as e:
            print(f"❌ Failed to hover over priority badge: {e}\n")

        # Test 7: Check loading states
        try:
            loading_visible = await page.is_visible('[data-testid="loading-state"]', timeout=1000)
            print(f"🔍 Loading state visible: {loading_visible}\n")
        except Exception as e:
            print(f"⚠️  Could not check loading state: {e}\n")

        # Test 8: Check error states
        try:
            error_visible = await page.is_visible('[data-testid="error-state"]', timeout=1000)
            print(f"🔍 Error state visible: {error_visible}\n")
        except Exception as e:
            print(f"⚠️  Could not check error state: {e}\n")

        # Wait a bit more to catch any delayed errors
        print("⏳ Waiting 3 seconds to catch any delayed errors...\n")
        await asyncio.sleep(3)

        # Final screenshot
        await page.screenshot(path='/Users/cliffclarke/Claude_Code/task-mcp/debug_screenshots/09_final_state.png')
        print("📸 Screenshot saved: 09_final_state.png\n")

        # Get final page state
        try:
            html_content = await page.content()
            with open('/Users/cliffclarke/Claude_Code/task-mcp/debug_screenshots/page_content.html', 'w') as f:
                f.write(html_content)
            print("📄 HTML content saved: page_content.html\n")
        except Exception as e:
            print(f"❌ Failed to save HTML content: {e}\n")

        print("="*80)
        print("📊 ERROR SUMMARY")
        print("="*80 + "\n")

        print(f"Console Errors: {len(console_errors)}")
        print(f"Console Warnings: {len(console_warnings)}")
        print(f"Page Errors: {len(page_errors)}")
        print(f"Network Errors: {len(network_errors)}")
        print(f"Total Issues: {len(console_errors) + len(console_warnings) + len(page_errors) + len(network_errors)}\n")

        # Save detailed error report as JSON
        error_report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'console_errors': len(console_errors),
                'console_warnings': len(console_warnings),
                'page_errors': len(page_errors),
                'network_errors': len(network_errors),
                'total': len(console_errors) + len(console_warnings) + len(page_errors) + len(network_errors)
            },
            'console_errors': console_errors,
            'console_warnings': console_warnings,
            'page_errors': page_errors,
            'network_errors': network_errors,
            'console_logs': console_logs
        }

        with open('/Users/cliffclarke/Claude_Code/task-mcp/debug_screenshots/error_report.json', 'w') as f:
            json.dump(error_report, f, indent=2)

        print("💾 Detailed error report saved: error_report.json\n")

        # Keep browser open for manual inspection
        print("🔍 Browser will remain open for 10 seconds for manual inspection...")
        await asyncio.sleep(10)

        await browser.close()
        print("\n✅ Debugging session complete!")

        return error_report

if __name__ == '__main__':
    # Create screenshots directory
    import os
    os.makedirs('/Users/cliffclarke/Claude_Code/task-mcp/debug_screenshots', exist_ok=True)

    # Run the debugging session
    report = asyncio.run(debug_task_viewer())
