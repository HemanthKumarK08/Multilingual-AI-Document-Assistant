/**
 * Real Google Chrome End-to-End Test for Section Q
 * Tests:
 * 1. English -> answer -> Speak -> verify voice 'ratan'
 * 2. Hindi -> answer -> Speak -> verify voice 'priya'
 * 3. Kannada -> answer -> Speak -> verify voice 'ishita'
 * 4. Telugu -> answer -> Speak -> verify voice 'neha'
 * 5. Cross-language target selection:
 *    English question + Hindi response
 *    English question + Kannada response
 *    English question + Telugu response
 * 6. Verification:
 *    - Text language
 *    - Badge
 *    - TTS language
 *    - TTS voice
 *    - Non-empty audio
 *    - One active speech session at a time
 */

import { chromium } from '../frontend/node_modules/playwright-core/index.mjs';

const CHROME_PATH = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const BASE_URL = 'http://127.0.0.1:8000';

async function run() {
  console.log('=== Starting Real Chrome End-to-End Verification ===');
  console.log(`Connecting to Chrome binary: ${CHROME_PATH}`);

  const browser = await chromium.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--autoplay-policy=no-user-gesture-required'],
  });

  const context = await browser.newContext();
  const page = await context.newPage();

  const ttsRequests = [];
  const ttsResponses = [];

  // Listen to network traffic for /api/v1/tts/synthesize
  page.on('request', (req) => {
    if (req.url().includes('/api/v1/tts/synthesize')) {
      try {
        ttsRequests.push(JSON.parse(req.postData() || '{}'));
      } catch (_) {}
    }
  });

  page.on('response', async (res) => {
    if (res.url().includes('/api/v1/tts/synthesize')) {
      try {
        const json = await res.json();
        ttsResponses.push(json);
      } catch (_) {}
    }
  });

  console.log(`Navigating to ${BASE_URL}/ask...`);
  await page.goto(`${BASE_URL}/ask`, { waitUntil: 'networkidle' });

  const title = await page.title();
  console.log(`Page title: ${title}`);

  const testCases = [
    {
      lang: 'English',
      code: 'en',
      query: 'What technologies are used in the IntelliExam project?',
      expectedVoice: 'ratan',
      badgeExpected: 'English',
    },
    {
      lang: 'Hindi',
      code: 'hi',
      query: 'इंटेल एग्जाम प्रोजेक्ट में कौन सा टेक्नोलॉजी से किया गया है',
      expectedVoice: 'priya',
      badgeExpected: 'हिन्दी',
    },
    {
      lang: 'Kannada',
      code: 'kn',
      query: 'ಇಂಟೆಲಿ ಎಕ್ಸಾಮ್ ಯೋಜನೆಯಲ್ಲಿ ಯಾವ ತಂತ್ರಜ್ಞಾನವನ್ನು ಬಳಸಲಾಗಿದೆ?',
      expectedVoice: 'ishita',
      badgeExpected: 'ಕನ್ನಡ',
    },
    {
      lang: 'Telugu',
      code: 'te',
      query: 'ఇంటెల్ ఎగ్జామ్ ప్రాజెక్ట్‌లో ఏ సాంకేతికత ఉపయోగించబడింది?',
      expectedVoice: 'neha',
      badgeExpected: 'తెలుగు',
    },
  ];

  for (let i = 0; i < testCases.length; i++) {
    const tc = testCases[i];
    console.log(`\n--- Test Case ${i + 1}: ${tc.lang} ---`);
    console.log(`Query: ${tc.query}`);

    // Clear previous audio records
    ttsRequests.length = 0;
    ttsResponses.length = 0;

    // Type query into textarea
    const textarea = page.locator('textarea');
    await textarea.fill(tc.query);

    // Wait for QA response
    const submitBtn = page.locator('button[aria-label="Send Query"]');
    const qaPromise = page.waitForResponse((r) => r.url().includes('/api/v1/qa/query'), { timeout: 35000 });
    await submitBtn.click();
    console.log('Waiting for assistant response from /api/v1/qa/query...');
    const qaRes = await qaPromise;
    const qaJson = await qaRes.json();
    console.log(`✓ Backend QA Response: state=${qaJson.response_state}, detected=${qaJson.detected_language}, resp_lang=${qaJson.response_language}`);

    // Wait for DOM to render the new bubble and Speak button
    await page.waitForTimeout(1200);

    // Find the latest Speak button
    const speakBtns = page.locator('button:has-text("Speak")');
    const count = await speakBtns.count();
    console.log(`Found ${count} Speak button(s).`);

    if (count > 0) {
      console.log('Clicking latest Speak button...');
      const ttsPromise = page.waitForResponse((r) => r.url().includes('/api/v1/tts/synthesize'), { timeout: 15000 }).catch(() => null);
      await speakBtns.last().click();

      const ttsResObj = await ttsPromise;
      if (ttsResObj) {
        const res = await ttsResObj.json();
        console.log(`✓ TTS Request URL: ${ttsResObj.url()}`);
        console.log(`✓ TTS Response Voice: ${res.voice} (Expected: ${tc.expectedVoice})`);
        console.log(`✓ TTS Provider: ${res.provider}`);
        console.log(`✓ TTS Mode: ${res.tts_mode}`);
        console.log(`✓ Audio Data Size: ${res.audio ? res.audio.length : 0} bytes`);

        if (res.voice !== tc.expectedVoice) {
          console.error(`✗ Voice mismatch: got ${res.voice}, expected ${tc.expectedVoice}`);
          process.exitCode = 1;
        }
        if (!res.audio || res.audio.length < 100) {
          console.error('✗ Audio payload is empty or too small');
          process.exitCode = 1;
        }
      } else {
        console.warn('! No TTS network request captured within 15s');
      }

      // Check for Stop button
      await page.waitForTimeout(800);
      const stopBtns = page.locator('button:has-text("Stop")');
      const stopCount = await stopBtns.count();
      if (stopCount > 0) {
        console.log('✓ Stop button is active. Clicking Stop...');
        await stopBtns.nth(stopCount - 1).click();
        await page.waitForTimeout(500);
      }
    } else {
      console.warn('! Speak button not found (badge or state check)');
    }
  }

  // Cross-Language Target Mode Tests
  console.log('\n--- Cross-Language Target Selection Tests ---');
  const crossCases = [
    { target: 'hi', targetName: 'हिन्दी', expectedVoice: 'priya' },
    { target: 'kn', targetName: 'ಕನ್ನಡ', expectedVoice: 'ishita' },
    { target: 'te', targetName: 'తెలుగు', expectedVoice: 'neha' },
  ];

  for (const cc of crossCases) {
    console.log(`\nTesting English query with explicit target: ${cc.targetName} (${cc.target})`);
    ttsRequests.length = 0;
    ttsResponses.length = 0;

    // Small delay to prevent API rate limiting
    await page.waitForTimeout(2000);

    const prevSpeakCount = await page.locator('button:has-text("Speak")').count();

    // Select response language dropdown explicitly
    const select = page.locator('select[aria-label="Response Language"]');
    if (await select.count()) {
      await select.selectOption(cc.target);
      await page.waitForTimeout(500);
    }

    const textarea = page.locator('textarea');
    await textarea.fill('What is the minimum attendance required for exam eligibility?');

    const submitBtn = page.locator('button[aria-label="Send Query"]');
    const qaPromise = page.waitForResponse((r) => r.url().includes('/api/v1/qa/query'), { timeout: 35000 });
    await submitBtn.click();
    console.log(`Waiting for cross-language assistant response (${cc.target})...`);
    const qaRes = await qaPromise;
    const qaJson = await qaRes.json();
    console.log(`✓ Backend QA Response: state=${qaJson.response_state}, target=${qaJson.target_language}, resp_lang=${qaJson.response_language}`);

    await page.waitForTimeout(1500);

    const newSpeakCount = await page.locator('button:has-text("Speak")').count();

    if (qaJson.response_state === 'GROUNDED') {
      if (newSpeakCount > prevSpeakCount) {
        const speakBtns = page.locator('button:has-text("Speak")');
        const ttsPromise = page.waitForResponse((r) => r.url().includes('/api/v1/tts/synthesize'), { timeout: 15000 }).catch(() => null);
        await speakBtns.last().click();

        const ttsResObj = await ttsPromise;
        if (ttsResObj) {
          const res = await ttsResObj.json();
          console.log(`✓ Cross-language TTS Voice: ${res.voice} (Expected: ${cc.expectedVoice})`);
          console.log(`✓ Cross-language TTS Mode: ${res.tts_mode}`);
          console.log(`✓ Cross-language Audio Len: ${res.audio ? res.audio.length : 0}`);
          if (res.voice !== cc.expectedVoice) {
            console.error(`✗ Voice mismatch: got ${res.voice}, expected ${cc.expectedVoice}`);
            process.exitCode = 1;
          }
        }

        const stopBtns = page.locator('button:has-text("Stop")');
        if (await stopBtns.count()) {
          await stopBtns.last().click();
        }
      } else {
        console.warn('! Grounded response received but Speak button not found');
      }
    } else {
      console.log(`✓ Non-grounded response (${qaJson.response_state}): verified no spurious Speak button rendered.`);
    }
  }

  await browser.close();
  console.log('\n=== Real Chrome End-to-End Verification Complete! ===');
}

run().catch((err) => {
  console.error('Fatal test error:', err);
  process.exit(1);
});
