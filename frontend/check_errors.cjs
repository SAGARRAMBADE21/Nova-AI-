import { chromium } from 'playwright';

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  const errors: string[] = [];
  page.on('console', msg => {
    if (msg.type() === 'error') {
      errors.push(msg.text());
    }
  });
  page.on('pageerror', err => {
    errors.push(err.message);
  });

  try {
    const response = await page.goto('http://localhost:5173', { waitUntil: 'networkidle' });
    console.log('Status:', response?.status());
    console.log('Errors found:', JSON.stringify(errors, null, 2));
  } catch (e) {
    console.error('Failed to load:', e);
  } finally {
    await browser.close();
  }
})();
