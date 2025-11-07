#!/usr/bin/env python3
"""
Capture console errors from the task viewer frontend.
Server should already be running on http://localhost:8001
"""

import json

from playwright.sync_api import sync_playwright


def capture_console_errors():
    console_messages = []
    errors = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Capture console messages
        def handle_console(msg):
            message_data = {
                'type': msg.type,
                'text': msg.text,
                'location': msg.location
            }
            console_messages.append(message_data)

            # Track errors and warnings
            if msg.type in ['error', 'warning']:
                errors.append(message_data)
                print(f"[{msg.type.upper()}] {msg.text}")
                if msg.location:
                    print(f"  Location: {msg.location}")

        # Capture page errors
        def handle_page_error(error):
            error_data = {
                'type': 'pageerror',
                'message': str(error)
            }
            errors.append(error_data)
            print(f"[PAGE ERROR] {error}")

        page.on('console', handle_console)
        page.on('pageerror', handle_page_error)

        print("Navigating to http://localhost:8001...")
        page.goto('http://localhost:8001')

        print("Waiting for page to load and Alpine.js to initialize...")
        page.wait_for_load_state('networkidle')

        # Wait a bit more for Alpine.js initialization
        page.wait_for_timeout(2000)

        # Take screenshot
        screenshot_path = '/tmp/task-viewer-screenshot.png'
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"\nScreenshot saved to: {screenshot_path}")

        # Get page title
        title = page.title()
        print(f"Page title: {title}")

        # Check if Alpine is loaded
        alpine_loaded = page.evaluate("() => typeof Alpine !== 'undefined'")
        print(f"Alpine.js loaded: {alpine_loaded}")

        # Try to interact with the page to trigger more errors
        print("\nAttempting to interact with page elements...")

        # Try clicking on various elements to trigger Alpine expressions
        try:
            # Wait for any projects to load
            page.wait_for_timeout(1000)

            # Try to select a project if the dropdown exists
            project_selector = page.locator('select').first
            if project_selector.count() > 0:
                print("Found project selector, attempting to interact...")
                project_selector.click()
                page.wait_for_timeout(500)
        except Exception as e:
            print(f"Interaction error: {e}")

        browser.close()

    # Summary
    print("\n" + "="*60)
    print(f"SUMMARY: Found {len(errors)} errors/warnings")
    print("="*60)

    if errors:
        print("\nAll Errors and Warnings:")
        for i, error in enumerate(errors, 1):
            print(f"\n{i}. [{error['type'].upper()}]")
            if 'text' in error:
                print(f"   {error['text']}")
            if 'message' in error:
                print(f"   {error['message']}")
            if 'location' in error and error['location']:
                print(f"   Location: {error['location']}")
    else:
        print("\n✅ No errors or warnings found!")

    # Save to JSON for analysis
    output_file = '/tmp/console-errors.json'
    with open(output_file, 'w') as f:
        json.dump({
            'total_messages': len(console_messages),
            'total_errors': len(errors),
            'errors': errors,
            'all_messages': console_messages
        }, f, indent=2)
    print(f"\nDetailed output saved to: {output_file}")

    return errors

if __name__ == '__main__':
    capture_console_errors()
