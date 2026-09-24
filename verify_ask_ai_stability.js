const http = require('http');
const fs = require('fs');

function httpGetJson(url) {
  return new Promise((resolve, reject) => {
    http.get(url, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try { resolve(JSON.parse(data)); } catch (e) { reject(e); }
      });
    }).on('error', reject);
  });
}

function sendCDP(ws, method, params = {}) {
  return new Promise((resolve, reject) => {
    const id = Math.floor(Math.random() * 1000000);
    const msg = JSON.stringify({ id, method, params });
    const handler = (event) => {
      const resp = JSON.parse(event.data);
      if (resp.id === id) {
        ws.removeEventListener('message', handler);
        if (resp.error) reject(resp.error);
        else resolve(resp.result);
      }
    };
    ws.addEventListener('message', handler);
    ws.send(msg);
  });
}

async function run() {
  console.log('Connecting to Chrome CDP...');
  const targets = await httpGetJson('http://127.0.0.1:9222/json');
  let target = targets.find(t => t.type === 'page' && t.url.includes(':8000'));
  if (!target) target = targets.find(t => t.type === 'page');
  if (!target) throw new Error('No page target found');

  const ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => {
    ws.addEventListener('open', resolve);
    ws.addEventListener('error', reject);
  });

  await sendCDP(ws, 'Page.enable');
  await sendCDP(ws, 'Runtime.enable');

  console.log('Navigating to http://localhost:8000/ask ...');
  await sendCDP(ws, 'Page.navigate', { url: 'http://localhost:8000/ask' });
  await new Promise(r => setTimeout(r, 2000));

  // Helper to send query via UI
  async function submitQueryViaUI(queryText) {
    return await sendCDP(ws, 'Runtime.evaluate', {
      expression: `(async () => {
        const textarea = document.querySelector('textarea');
        const sendBtn = document.querySelector('button[aria-label="Send Query"]');
        if (!textarea) return { error: 'no textarea' };

        const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set;
        nativeSetter.call(textarea, ${JSON.stringify(queryText)});
        textarea.dispatchEvent(new Event('input', { bubbles: true }));
        await new Promise(r => setTimeout(r, 100));

        const btn = document.querySelector('button[aria-label="Send Query"]');
        if (btn && !btn.disabled) {
          btn.click();
          return { submitted: true };
        }
        return { error: 'send button disabled' };
      })()`,
      awaitPromise: true,
      returnByValue: true
    });
  }

  // 1. Submit English query
  console.log('1. Submitting English query...');
  const q1 = await submitQueryViaUI('What is the minimum attendance required for semester examinations?');
  console.log('Q1 submit status:', q1.result.value);
  await new Promise(r => setTimeout(r, 2000));

  // 2. Submit Hindi query
  console.log('2. Submitting Hindi query...');
  const q2 = await submitQueryViaUI('उपस्थिति नियम क्या हैं?');
  console.log('Q2 submit status:', q2.result.value);
  await new Promise(r => setTimeout(r, 2000));

  // 3. Submit Kannada query
  console.log('3. Submitting Kannada query...');
  const q3 = await submitQueryViaUI('ಹಾಜರಾತಿ ನಿಯಮಗಳು ಯಾವುವು?');
  console.log('Q3 submit status:', q3.result.value);
  await new Promise(r => setTimeout(r, 2000));

  // 4. Submit Telugu query
  console.log('4. Submitting Telugu query...');
  const q4 = await submitQueryViaUI('హాజరు నియమాలు ఏమిటి?');
  console.log('Q4 submit status:', q4.result.value);
  await new Promise(r => setTimeout(r, 2000));

  // Inspect rendered messages in DOM
  const domInspection = await sendCDP(ws, 'Runtime.evaluate', {
    expression: `(() => {
      const messages = Array.from(document.querySelectorAll('.prose')).map(p => p.textContent.substring(0, 100));
      const badges = Array.from(document.querySelectorAll('.rounded-full')).map(b => b.textContent.trim()).filter(Boolean);
      const citations = document.querySelectorAll('.grid, [class*="citation"]').length;
      return {
        messageCount: messages.length,
        messagesSnippet: messages,
        badges: badges.slice(0, 10),
        hasCitations: citations > 0
      };
    })()`,
    returnByValue: true
  });
  console.log('DOM Inspection with 4 Turns (8 messages):', domInspection.result.value);

  // 5. Measure Typing Latency with 8 messages in DOM
  console.log('5. Measuring Keystroke Latency on composer...');
  const typingBenchmark = await sendCDP(ws, 'Runtime.evaluate', {
    expression: `(() => {
      const textarea = document.querySelector('textarea');
      const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set;
      const testStr = 'Testing typing latency across long conversation history...';
      const times = [];
      for (let i = 0; i < testStr.length; i++) {
        const t0 = performance.now();
        nativeSetter.call(textarea, testStr.substring(0, i + 1));
        textarea.dispatchEvent(new Event('input', { bubbles: true }));
        times.push(performance.now() - t0);
      }
      const sum = times.reduce((a, b) => a + b, 0);
      return {
        keystrokes: testStr.length,
        totalMs: sum,
        avgMsPerKeystroke: sum / testStr.length,
        maxMs: Math.max(...times),
        minMs: Math.min(...times)
      };
    })()`,
    returnByValue: true
  });
  console.log('Typing Benchmark Result:', typingBenchmark.result.value);

  // Capture screenshot of the full multi-turn conversation
  const screenshot = await sendCDP(ws, 'Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync('ask_ai_multi_turn_verified.png', Buffer.from(screenshot.data, 'base64'));
  console.log('Saved screenshot: ask_ai_multi_turn_verified.png');

  ws.close();
}

run().catch(console.error);
