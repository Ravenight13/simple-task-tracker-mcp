#!/usr/bin/env node

/**
 * Test Alpine.js Frontend for Errors
 *
 * This script uses puppeteer to load the task viewer frontend
 * and capture any console errors, especially Alpine.js expression errors.
 */

const puppeteer = require('puppeteer');

async function testFrontend() {
  console.log('🧪 Testing Task Viewer Frontend for Alpine.js Errors\n');

  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();

  // Collect console messages
  const consoleMessages = [];
  const errors = [];

  page.on('console', msg => {
    const type = msg.type();
    const text = msg.text();
    consoleMessages.push({ type, text });

    if (type === 'error') {
      errors.push(text);
      console.log(`❌ Console Error: ${text}`);
    } else if (type === 'warning') {
      console.log(`⚠️  Console Warning: ${text}`);
    }
  });

  // Capture page errors
  page.on('pageerror', error => {
    errors.push(error.message);
    console.log(`❌ Page Error: ${error.message}`);
  });

  try {
    console.log('📄 Loading page: http://localhost:8002/static/index.html\n');

    // Load the page
    await page.goto('http://localhost:8002/static/index.html', {
      waitUntil: 'networkidle2',
      timeout: 10000
    });

    // Wait for Alpine to initialize
    await page.waitForTimeout(2000);

    // Set API key in localStorage
    await page.evaluate(() => {
      localStorage.setItem('task_viewer_api_key', 'quJ5dpjJHfhuskKj3CGcTxn5Af6HZ-O9mPkaepvH7fo');
    });

    // Reload to use the API key
    console.log('🔄 Reloading with API key...\n');
    await page.reload({ waitUntil: 'networkidle2' });

    // Wait for data to load
    await page.waitForTimeout(3000);

    // Check for Alpine.js errors specifically
    const alpineErrors = errors.filter(e =>
      e.includes('Alpine') ||
      e.includes('Uncaught') ||
      e.includes('Cannot read') ||
      e.includes('undefined')
    );

    console.log('\n📊 Test Results:');
    console.log('================');
    console.log(`Total Console Messages: ${consoleMessages.length}`);
    console.log(`Total Errors: ${errors.length}`);
    console.log(`Alpine-Related Errors: ${alpineErrors.length}`);

    if (errors.length === 0) {
      console.log('\n✅ SUCCESS: No errors detected!');
    } else {
      console.log('\n❌ FAILED: Errors detected:');
      errors.forEach((err, i) => {
        console.log(`  ${i + 1}. ${err}`);
      });
    }

    // Take screenshot
    await page.screenshot({
      path: '/Users/cliffclarke/Claude_Code/task-mcp/test-screenshot.png',
      fullPage: true
    });
    console.log('\n📸 Screenshot saved to: test-screenshot.png');

    // Get page title
    const title = await page.title();
    console.log(`📄 Page Title: ${title}`);

    // Check if Alpine initialized
    const alpineInitialized = await page.evaluate(() => {
      return typeof Alpine !== 'undefined';
    });
    console.log(`🎯 Alpine.js Initialized: ${alpineInitialized ? '✅' : '❌'}`);

  } catch (error) {
    console.error('\n❌ Test failed with exception:', error.message);
    errors.push(error.message);
  } finally {
    await browser.close();
  }

  return errors.length === 0;
}

// Run the test
testFrontend()
  .then(success => {
    process.exit(success ? 0 : 1);
  })
  .catch(error => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
