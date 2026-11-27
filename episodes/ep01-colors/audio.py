# Synthesizes an original cheerful kids' track + sound effects, synced to the animation timeline.
import numpy as np, wave, sys
SR = 44100
DUR = 24.0
N = int(SR * DUR)
rng = np.random.default_rng(3)

def tt(d): return np.arange(int(SR * d)) / SR
def add(buf, start, sig, gain=1.0):
    i = int(start * SR)
    if i >= len(buf): return
    j = min(len(buf), i + len(sig))
    buf[i:j] += sig[:j - i] * gain
def midi(m): return 440.0 * 2 ** ((m - 69) / 12)
def env_ad(n, a=0.005, decay=0.3):
    t = np.arange(n) / SR
    e = np.exp(-t / decay)
    na = max(1, int(a * SR)); e[:na] *= np.linspace(0, 1, na)
    return e

def pluck(freq, dur=0.9, bright=0.5):
    # Karplus-Strong plucked string (ukulele-ish)
    n = int(SR * dur); p = max(2, int(SR / freq))
    buf = rng.uniform(-1, 1, p)
    out = np.zeros(n)
    for i in range(n):
        out[i] = buf[i % p]
        nxt = buf[(i + 1) % p]
        buf[i % p] = 0.996 * (bright * buf[i % p] + (1 - bright) * 0.5 * (buf[i % p] + nxt))
    return out * env_ad(n, 0.002, dur * 0.6)

def glock(freq, dur=0.8):
    t = tt(dur)
    s = (np.sin(2*np.pi*freq*t) + 0.35*np.sin(2*np.pi*freq*2.76*t)*np.exp(-t/0.08) + 0.2*np.sin(2*np.pi*freq*5.4*t)*np.exp(-t/0.03))
    return s * env_ad(len(t), 0.002, 0.35)

def bass(freq, dur=0.45):
    t = tt(dur)
    s = np.sin(2*np.pi*freq*t) + 0.25*np.sin(2*np.pi*freq*2*t)
    return s * env_ad(len(t), 0.01, 0.25)

def kick():
    t = tt(0.25); f = 110*np.exp(-t/0.05)+45
    return np.sin(2*np.pi*np.cumsum(f)/SR) * env_ad(len(t), 0.001, 0.09)

def noise(dur): return rng.uniform(-1, 1, int(SR*dur))
def hp(x, a=0.85):  # simple one-pole highpass
    y = np.zeros_like(x); prev = 0; px = 0
    for i, v in enumerate(x): prev = a*(prev + v - px); px = v; y[i] = prev
    return y
def lp(x, a=0.2):
    y = np.zeros_like(x); prev = 0
    for i, v in enumerate(x): prev = prev + a*(v - prev); y[i] = prev
    return y

music = np.zeros(N); sfx = np.zeros(N)

# ---------------- MUSIC: 120 bpm, C - G - Am - F ----------------
bpm = 120; beat = 60 / bpm; bar = 4 * beat
chords = [[60, 64, 67, 72], [59, 62, 67, 71], [57, 60, 64, 69], [57, 60, 65, 69]]
roots = [48, 43, 45, 41]
melody = [  # (beat offset within 2-bar phrase, midi, dur)
    (0, 76, .5), (.5, 79, .5), (1, 81, .5), (1.5, 79, .5), (2, 76, 1), (3, 74, .5), (3.5, 72, .5),
    (4, 74, .5), (4.5, 76, .5), (5, 79, .5), (5.5, 76, .5), (6, 74, 1.5), (7.5, 72, .5)]
strum = [0, 1, 1.5, 2.5, 3, 3.5]
nb = int(DUR / bar) + 1
pl_cache = {}
for b in range(nb):
    t0 = b * bar; ch = chords[b % 4]
    for s in strum:
        for k, m in enumerate(ch):
            key = (m, s % 1 == 0)
            if key not in pl_cache: pl_cache[key] = pluck(midi(m), 0.7, 0.45 if s % 1 == 0 else 0.6)
            add(music, t0 + s*beat + k*0.012, pl_cache[key], 0.09 if s % 1 == 0 else 0.06)
    add(music, t0, bass(midi(roots[b % 4])), 0.35); add(music, t0 + 2*beat, bass(midi(roots[b % 4])), 0.3)
    add(music, t0, kick(), 0.5); add(music, t0 + 2*beat, kick(), 0.45)
    for k in (1, 3):  # soft clap
        c = hp(noise(0.12), 0.7) * env_ad(int(SR*0.12), 0.001, 0.03)
        add(music, t0 + k*beat, c, 0.12)
    for k in range(8):  # shaker
        sh = hp(noise(0.06), 0.5) * env_ad(int(SR*0.06), 0.004, 0.015)
        add(music, t0 + k*beat/2, sh, 0.05 if k % 2 else 0.03)
    if b % 2 == 0 and t0 >= 2*bar - 0.01:  # melody enters after intro
        for off, m, d in melody:
            add(music, t0 + off*beat, glock(midi(m), d + 0.4), 0.11)

# fade in / out
fi = int(0.05*SR); music[:fi] *= np.linspace(0, 1, fi)
fo = int(1.2*SR); music[-fo:] *= np.linspace(1, 0, fo)

# ---------------- SFX ----------------
def whoosh(dur=0.7, up=True):
    n = noise(dur); t = tt(dur)
    a = np.linspace(0.05, 0.5, len(t)) if up else np.linspace(0.5, 0.05, len(t))
    y = np.zeros_like(n); prev = 0
    for i, v in enumerate(n): prev = prev + a[i]*(v-prev); y[i] = prev
    return y * np.sin(np.pi*np.linspace(0, 1, len(t)))**1.5
def boing(f0=180, f1=520, dur=0.45):
    t = tt(dur); f = f0 + (f1-f0)*(1-np.exp(-t/0.08)) + 40*np.sin(2*np.pi*14*t)*np.exp(-t/0.2)
    return np.sin(2*np.pi*np.cumsum(f)/SR) * env_ad(len(t), 0.003, 0.18)
def thump():
    t = tt(0.3); f = 90*np.exp(-t/0.06)+40
    return np.sin(2*np.pi*np.cumsum(f)/SR) * env_ad(len(t), 0.001, 0.08) + 0.3*lp(noise(0.3), 0.08)*env_ad(len(t), 0.001, 0.04)
def pop():
    n = hp(noise(0.18), 0.6) * env_ad(int(SR*0.18), 0.0005, 0.025)
    return n*1.4 + thump()[:len(n)]*0.8
def chime(base=84):
    out = np.zeros(int(SR*1.2))
    for k, m in enumerate([base, base+4, base+7, base+12]):
        g = glock(midi(m), 0.9); i = int(k*0.06*SR); out[i:i+len(g)] += g[:len(out)-i]
    return out
def blip(m):
    t = tt(0.16); return np.sin(2*np.pi*midi(m)*t)*env_ad(len(t), 0.002, 0.06) + 0.3*np.sin(2*np.pi*midi(m)*2*t)*env_ad(len(t), 0.002, 0.03)
def squeak(dur=2.0):
    t = tt(dur); f = 260 + 520*(t/dur)**2 + 25*np.sin(2*np.pi*7*t)
    s = np.sin(2*np.pi*np.cumsum(f)/SR) + 0.3*np.sin(2*np.pi*2*np.cumsum(f)/SR)
    e = np.ones_like(t); e *= (0.15 + 0.85*(t/dur)); e *= (0.6 + 0.4*np.sin(2*np.pi*3.5*t)**2)
    fade = int(0.08*SR); e[:fade] *= np.linspace(0, 1, fade); e[-fade:] *= np.linspace(1, 0, fade)
    return s*e
def tada():
    out = np.zeros(int(SR*1.6))
    for k, m in enumerate([72, 76, 79, 84, 88]):
        g = glock(midi(m), 1.0); i = int(k*0.07*SR); out[i:i+len(g)] += g[:len(out)-i]
    return out

add(sfx, 0.0, whoosh(1.1), 0.35)           # balloons rising
add(sfx, 0.05, chime(84), 0.25)            # hook text sparkle
add(sfx, 0.3, boing(160, 560, 0.5), 0.35)  # camel jumps in
add(sfx, 1.0, thump(), 0.55)               # lands
add(sfx, 0.95, blip(84), 0.15)             # "guess with me" pop-in
add(sfx, 2.55, chime(79), 0.2)             # hello
for tStart, tPop, tEnd in [(6.0, 8.6, 10.4), (10.5, 13.1, 14.9), (15.0, 17.6, 19.4)]:
    add(sfx, tStart, whoosh(0.45), 0.25)
    add(sfx, tStart + .5, squeak(tPop - tStart - .55), 0.06)
    for k, m in enumerate([72, 74, 76]): add(sfx, tPop - 1.6 + k*.5, blip(m), 0.28)   # 3,2,1
    add(sfx, tPop, pop(), 0.75)
    add(sfx, tPop + .05, tada(), 0.3)
    add(sfx, tPop + .12, boing(220, 640, 0.4), 0.18)  # happy jump
    add(sfx, tEnd - .75, whoosh(0.7, up=False), 0.2)  # fruit flies to its place
    add(sfx, tEnd, thump(), 0.35)
add(sfx, 19.5, tada(), 0.35)
add(sfx, 19.55, whoosh(1.0), 0.2)
add(sfx, 22.35, chime(84), 0.3)

def save(name, x):
    x = x / max(1e-9, np.max(np.abs(x))) * 0.98 if np.max(np.abs(x)) > 0.98 else x
    y = np.int16(np.clip(x, -1, 1) * 32767)
    st = np.stack([y, y], axis=1)
    with wave.open(name, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes())

save('music.wav', music * 0.9)
save('sfx.wav', sfx)
mix = music * 0.75 + sfx
save('mix.wav', mix)
print('ok peak', np.max(np.abs(mix)))
