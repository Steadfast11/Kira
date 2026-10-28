#!/usr/bin/env python3
# Astra project — Copyright (c) 2026 Xasan Abdukhafizov.
"""Kira's boot voice and sounds, made on this Mac and the same on every run.

  tools/make_boot_voice.py                every line of ui/boot/lines.json with Kokoro, the two sounds, and timings.json
  tools/make_boot_voice.py --align-only   keep the .m4a files (your own recordings) and redo timings.json from them
  tools/make_boot_voice.py --kokoro DIR   the folder with kokoro-v1.0.onnx and voices-v1.0.bin

Each line is trimmed, given a soft start and end, set to -19 LUFS (the sounds to -26 and -24, under the voice) and saved as
48 kHz AAC. timings.json says when each word starts (ms), so the page shows every word as it is spoken: the pauses in the audio
place the phrases, then each word gets its share of its phrase (Kokoro's own length for that word, or its syllables for a
recording) and its start moves to the quietest moment nearby. Needs numpy, ffmpeg or afconvert, and kokoro-onnx to synthesize.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import wave

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOT = os.path.join(ROOT, 'ui', 'boot')
RATE = 48000
KOKORO_DIRS = [os.path.expanduser('~/.config/kira/kokoro'), os.path.expanduser('~/.cache/jarvis/kokoro')]


def read_wav(path):
    with wave.open(path) as f:
        rate, n, width, channels = f.getframerate(), f.getnframes(), f.getsampwidth(), f.getnchannels()
        data = np.frombuffer(f.readframes(n), dtype={2: np.int16, 4: np.int32}[width]).astype(np.float64)
    data = data.reshape(-1, channels).mean(axis=1) / (32768.0 if width == 2 else 2147483648.0)
    return data, rate


def write_wav(path, samples, rate):
    with wave.open(path, 'wb') as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(rate)
        f.writeframes((np.clip(samples, -1, 1) * 32767).astype(np.int16).tobytes())


def resample(samples, src, dst):
    if src == dst: return samples
    t = np.arange(int(len(samples) * dst / src)) * src / dst
    return np.interp(t, np.arange(len(samples)), samples)


def envelope(samples, rate, ms=10):
    hop = int(rate * ms / 1000)
    frames = len(samples) // hop
    return np.sqrt(np.mean(samples[:frames * hop].reshape(frames, hop) ** 2, axis=1) + 1e-12)


def trim(samples, rate):
    """Silence off both ends, keeping 30 ms so no consonant is clipped."""
    env = envelope(samples, rate)
    voiced = np.nonzero(env > env.max() * 0.04)[0]
    if not len(voiced): return samples
    hop = rate // 100
    a, b = max(0, voiced[0] * hop - rate * 30 // 1000), min(len(samples), (voiced[-1] + 1) * hop + rate * 30 // 1000)
    return samples[a:b]


def soften(samples, rate, lead=0.08, tail=0.30, fade_in=0.025, fade_out=0.16):
    """A little silence before and after, and a raised-cosine fade at each end: no click, no hard attack."""
    n_in, n_out = int(rate * fade_in), int(rate * fade_out)
    s = samples.copy()
    s[:n_in] *= 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, n_in))
    s[-n_out:] *= 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, n_out))
    return np.concatenate([np.zeros(int(rate * lead)), s, np.zeros(int(rate * tail))])


def syllables(word):
    return max(1, len(re.findall(r'[aeiouy]+', word.lower().rstrip('e') or word.lower())))


def align(samples, rate, words, weights):
    """Word start times in ms: phrases from the audio's pauses, words within a phrase by weight, snapped to the quietest frame."""
    env = envelope(samples, rate)
    loud = env > env.max() * 0.05
    voiced = np.nonzero(loud)[0]
    if not len(voiced) or not words: return [0] * len(words)
    first, last = int(voiced[0]), int(voiced[-1]) + 1
    gaps, i = [], first
    while i < last:   # quiet runs of 110 ms or more inside the speech
        if not loud[i]:
            j = i
            while j < last and not loud[j]: j += 1
            if j - i >= 11: gaps.append((i, j))
            i = j
        else: i += 1
    phrases, cur = [], []
    for k, w in enumerate(words):
        cur.append(k)
        if re.search(r'[.,!?;:]$', w) and k < len(words) - 1: phrases.append(cur); cur = []
    if cur: phrases.append(cur)
    while len(phrases) > 1 and len(gaps) < len(phrases) - 1:   # fewer pauses than punctuation: the last phrases share one span
        phrases[-2:] = [phrases[-2] + phrases[-1]]
    cut = sorted(sorted(gaps, key=lambda g: g[0] - g[1])[:len(phrases) - 1])   # the longest pauses, back in time order
    spans = [(first if n == 0 else cut[n - 1][1], last if n == len(phrases) - 1 else cut[n][0]) for n in range(len(phrases))]
    starts = [0] * len(words)
    for (a, b), phrase in zip(spans, phrases):
        w = np.array([weights[k] for k in phrase], dtype=float)
        edges = a + (b - a) * np.concatenate([[0], np.cumsum(w)[:-1]]) / w.sum()
        for n, (k, e) in enumerate(zip(phrase, edges)):
            if n == 0: starts[k] = a; continue
            lo, hi = max(a + 1, int(e) - 7), min(b - 1, int(e) + 7)   # ±70 ms
            starts[k] = lo + int(np.argmin(env[lo:hi + 1])) if hi > lo else int(e)
    return [int(s) * 10 for s in starts]


def ffmpeg():
    return shutil.which('ffmpeg') or next((p for p in ('/opt/homebrew/bin/ffmpeg', '/usr/local/bin/ffmpeg') if os.path.exists(p)), None)


def encode(samples, rate, path, lufs, voice=False):
    """48 kHz mono AAC at the given loudness: ffmpeg measures it (EBU R128), applies that one gain, and a soft limiter keeps
    the rare peak under -1.5 dBFS. The voice first goes through a gentle 2.5:1 compressor, so the limiter seldom acts."""
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, 'in.wav'); write_wav(src, resample(samples, rate, RATE), RATE)
        ff = ffmpeg()
        if ff:
            squeeze = 'acompressor=threshold=-26dB:ratio=2.5:attack=6:release=140:knee=6,' if voice else ''
            probe = subprocess.run([ff, '-hide_banner', '-nostats', '-i', src, '-af', f'{squeeze}ebur128', '-f', 'null', '-'], capture_output=True, text=True).stderr
            measured = float(re.findall(r'I:\s+(-?[\d.]+) LUFS', probe)[-1])
            norm = f'{squeeze}volume={lufs - measured:.2f}dB,alimiter=limit=0.84:attack=3:release=60:level=false'
            subprocess.run([ff, '-hide_banner', '-loglevel', 'error', '-y', '-i', src, '-af', norm, '-ac', '1', '-ar', str(RATE),
                            '-c:a', 'aac', '-b:a', '112k', '-map_metadata', '-1', '-fflags', '+bitexact', '-flags:a', '+bitexact', path], check=True)
        else:   # afconvert ships with macOS: plain RMS gain toward the target, then AAC
            s = resample(samples, rate, RATE)
            rms = np.sqrt(np.mean(s[np.abs(s) > 1e-4] ** 2)) or 1
            write_wav(src, s * min(10 ** ((lufs + 3.0) / 20) / rms, 0.7 / max(1e-6, np.abs(s).max())), RATE)
            subprocess.run(['/usr/bin/afconvert', '-f', 'm4af', '-d', 'aac', '-b', '112000', '-c', '1', src, path], check=True)


def decode(path):
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, 'out.wav')
        ff = ffmpeg()
        cmd = [ff, '-hide_banner', '-loglevel', 'error', '-y', '-i', path, '-ac', '1', '-ar', str(RATE), out] if ff else \
              ['/usr/bin/afconvert', '-f', 'WAVE', '-d', f'LEI16@{RATE}', '-c', '1', path, out]
        subprocess.run(cmd, check=True)
        return read_wav(out)


def pad_sound(rate=RATE):
    """The rise: an airy E-major pad that swells with the drop, gliding up a quarter tone, with a breath of filtered air."""
    seconds, rng = 5.2, np.random.default_rng(7)
    t = np.arange(int(rate * seconds)) / rate
    phase = np.cumsum(2 ** (0.25 / 12 * np.clip(t / 3.2, 0, 1))) / rate
    out = np.zeros_like(t)
    for f, a in ((164.81, .50), (246.94, .34), (329.63, .32), (415.30, .14), (493.88, .18), (739.99, .06)):
        out += a * 0.5 * (np.sin(2 * np.pi * (f - .55) * phase) + np.sin(2 * np.pi * (f + .55) * phase))   # a slow beat, like air in glass
    k, acc, air = np.exp(-2 * np.pi * 2400 / rate), 0.0, rng.standard_normal(len(t))
    for i, x in enumerate(air): acc = (1 - k) * x + k * acc; air[i] = acc   # one-pole low-pass at about 2.4 kHz
    air -= np.convolve(air, np.ones(64) / 64, mode='same')   # and no rumble under about 400 Hz
    out = out / 1.6 + air * 0.9 * np.exp(-((t - 2.3) / 1.1) ** 2)   # the breath peaks as the drop lets go
    u = np.clip(t / 1.7, 0, 1)
    env = u * u * (3 - 2 * u) * np.where(t > 3.6, 0.5 + 0.5 * np.cos(np.pi * np.clip((t - 3.6) / (seconds - 3.6), 0, 1)), 1)   # 1.7 s in, long release
    return out * env


def chime_sound(rate=RATE):
    """One soft glass bell (E6): a 90 ms rise, a long ring, a 400 ms fade at the end."""
    seconds = 3.0
    t = np.arange(int(rate * seconds)) / rate
    out = np.zeros_like(t)
    for ratio, a, decay in ((1, 1, 1.7), (2.0, .30, 1.05), (2.92, .16, .72), (4.16, .07, .46), (5.43, .035, .3)):
        out += a * np.sin(2 * np.pi * 1318.51 * ratio * t) * np.exp(-t / decay)
    out *= np.clip(t / 0.09, 0, 1) ** 2
    tail = int(rate * 0.4); out[-tail:] *= 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, tail))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--align-only', action='store_true')
    ap.add_argument('--kokoro')
    args = ap.parse_args()
    with open(os.path.join(BOOT, 'lines.json')) as f: cfg = json.load(f)
    lines = {k: v.replace('{WORDMARK}', cfg['wordmark']) for k, v in cfg['lines'].items()}
    kokoro = None
    if not args.align_only:
        folder = args.kokoro or next((d for d in KOKORO_DIRS if os.path.exists(os.path.join(d, 'kokoro-v1.0.onnx'))), None)
        if not folder: sys.exit('Kokoro model files not found; pass --kokoro DIR (kokoro-v1.0.onnx and voices-v1.0.bin).')
        try: from kokoro_onnx import Kokoro
        except ImportError: sys.exit('kokoro-onnx is missing for this Python: pip install kokoro-onnx')
        kokoro = Kokoro(os.path.join(folder, 'kokoro-v1.0.onnx'), os.path.join(folder, 'voices-v1.0.bin'))
    say = lambda text: kokoro.create(text, voice=cfg['voice'], speed=cfg['speed'], lang=cfg['lang'])
    out = {'voice': cfg['voice'] if kokoro else 'recorded', 'wordmark': cfg['wordmark'], 'lines': {}, 'sounds': {}}
    for key, text in lines.items():
        path, words = os.path.join(BOOT, key + '.m4a'), text.split()
        if kokoro:
            samples, rate = say(text)
            samples = soften(trim(np.asarray(samples, dtype=np.float64), rate), rate)
            weights = [len(trim(np.asarray(say(re.sub(r"[^\w']", '', w) or w)[0], dtype=np.float64), rate)) for w in words]
            encode(samples, rate, path, -19, voice=True)
        else:
            if not os.path.exists(path): sys.exit(f'Missing {path}: record it, or run without --align-only.')
            weights = [syllables(w) for w in words]
        samples, rate = decode(path)   # align on the file as saved, so the times match what plays
        out['lines'][key] = {'text': text, 'ms': int(len(samples) * 1000 / rate), 'words': [[w, t] for w, t in zip(words, align(samples, rate, words, weights))]}
        print(f'{key:9} {out["lines"][key]["ms"]:5} ms  ' + ' '.join(f'{w}@{t}' for w, t in out['lines'][key]['words']))
    for key, make, lufs in (('rise', pad_sound, -26), ('chime', chime_sound, -24)):
        path = os.path.join(BOOT, key + '.m4a')
        if not args.align_only or not os.path.exists(path): encode(make(), RATE, path, lufs)
        out['sounds'][key] = int(len(decode(path)[0]) * 1000 / RATE)
    with open(os.path.join(BOOT, 'timings.json'), 'w') as f: json.dump(out, f, indent=1, ensure_ascii=False); f.write('\n')
    print('Wrote', os.path.relpath(os.path.join(BOOT, 'timings.json'), ROOT))


if __name__ == '__main__':
    main()
