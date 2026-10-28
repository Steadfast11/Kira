#!/usr/bin/env python3
# Astra project — Copyright (c) 2026 Xasan Abdukhafizov.
"""Kira's voice: Kokoro (on-device, ONNX) kept loaded, so a short line starts in about 0.2 s.

  kokoro_say.py <model dir>        the dir holds kokoro-v1.0.onnx and voices-v1.0.bin
stdin, one JSON per line:   {"say": "text"}   {"stop": true}   {"voice": "af_heart", "speed": 1.05}
stdout, one JSON per line:  {"ready": true}   {"idle": true} (the queue ran dry or was stopped)
Exit code 2: Kokoro or its files are missing (the app falls back to the system voice).
"""
import json
import os
import queue
import subprocess
import sys
import tempfile
import threading
import wave


def emit(value):
    sys.stdout.write(json.dumps(value) + '\n')
    sys.stdout.flush()


def main():
    folder = sys.argv[1] if len(sys.argv) > 1 else ''
    model, voices = os.path.join(folder, 'kokoro-v1.0.onnx'), os.path.join(folder, 'voices-v1.0.bin')
    if not (os.path.isfile(model) and os.path.isfile(voices)):
        return 2
    try:
        import numpy as np
        from kokoro_onnx import Kokoro
        kokoro = Kokoro(model, voices)
    except Exception:
        return 2
    settings = {'voice': 'af_heart', 'speed': 1.05, 'lang': 'en-us'}
    lines, lock = queue.Queue(), threading.Lock()
    state = {'epoch': 0, 'player': None}

    def play(samples, rate, epoch):
        fd, path = tempfile.mkstemp(prefix='kira-say-', suffix='.wav')
        os.close(fd)
        try:
            with wave.open(path, 'wb') as out:
                out.setnchannels(1); out.setsampwidth(2); out.setframerate(rate)
                out.writeframes((np.clip(samples, -1, 1) * 32767).astype(np.int16).tobytes())
            with lock:
                if epoch != state['epoch']:
                    return
                state['player'] = subprocess.Popen(['/usr/bin/afplay', path])
            state['player'].wait()
        finally:
            try: os.remove(path)
            except OSError: pass

    def worker():
        try: kokoro.create('Ready.', voice=settings['voice'], speed=settings['speed'], lang='en-us')   # the first synthesis is the slow one
        except Exception: pass
        emit({'ready': True})
        while True:
            text, epoch, options = lines.get()
            if epoch == state['epoch']:
                try:
                    samples, rate = kokoro.create(text, voice=options['voice'], speed=options['speed'], lang=options['lang'])
                    if epoch == state['epoch']: play(samples, rate, epoch)
                except Exception:
                    pass
            if lines.empty(): emit({'idle': True})

    threading.Thread(target=worker, daemon=True).start()
    for raw in sys.stdin:
        try: message = json.loads(raw)
        except ValueError: continue
        if not isinstance(message, dict): continue
        if message.get('stop'):
            with lock:
                state['epoch'] += 1
                if state['player'] and state['player'].poll() is None: state['player'].terminate()
            while not lines.empty():
                try: lines.get_nowait()
                except queue.Empty: break
            emit({'idle': True})
        elif isinstance(message.get('say'), str) and message['say'].strip():
            options = {**settings, **{key: message[key] for key in ('voice', 'lang') if isinstance(message.get(key), str)}}
            lines.put((message['say'], state['epoch'], options))
        else:
            for key in ('voice', 'speed'):
                if key in message: settings[key] = message[key]
    return 0


if __name__ == '__main__':
    sys.exit(main())
