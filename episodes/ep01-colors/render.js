// usage: node render.js preview t1 t2 ...   -> writes preview_<t>.png
//        node render.js video out.mp4 [fps]  -> pipes frames to ffmpeg (silent video)
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');
(async () => {
  const mode = process.argv[2];
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  page.on('pageerror', e => console.error('PAGE ERROR', e.message));
  await page.goto('file://' + path.join(__dirname, 'index.html'));
  await page.evaluate(() => document.fonts.ready);
  await page.evaluate(async () => { await document.fonts.load('800 100px Baloo', 'مرحبا'); });
  if (mode === 'preview') {
    for (const t of process.argv.slice(3)) {
      await page.evaluate(t => window.render(t), parseFloat(t));
      await page.screenshot({ path: path.join(__dirname, `preview_${t}.png`) });
    }
  } else {
    const out = process.argv[3]; const fps = parseInt(process.argv[4] || '30');
    const dur = await page.evaluate(() => window.DUR);
    const n = Math.round(dur * fps);
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-',
      '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
    const t0 = Date.now();
    for (let i = 0; i < n; i++) {
      await page.evaluate(t => window.render(t), i / fps);
      const buf = await page.screenshot({ type: 'jpeg', quality: 94 });
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      if (i % 90 === 0) console.log(`frame ${i}/${n} ${((Date.now() - t0) / 1000).toFixed(0)}s`);
    }
    ff.stdin.end();
    await new Promise(r => ff.on('close', r));
  }
  await browser.close();
})();
