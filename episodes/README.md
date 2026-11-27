# Bunduq episodes

Each folder is one YouTube Short (1080x1920, 30fps), drawn and animated in code.

Build an episode:

```bash
cd episodes/ep01-colors
python3 audio.py                     # music + sound effects -> mix.wav
node render.js video silent.mp4 30   # frames -> silent.mp4 (needs Playwright + ffmpeg)
ffmpeg -i silent.mp4 -i mix.wav -map 0:v -map 1:a -c:v copy \
  -af "loudnorm=I=-14:TP=-1.5" -c:a aac -b:a 192k -shortest out.mp4
```

Preview single frames: `node render.js preview 0 3.5 9`

Font: Baloo Bhaijaan 2 (SIL Open Font License).
